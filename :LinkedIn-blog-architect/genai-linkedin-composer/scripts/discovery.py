#!/usr/bin/env python3
"""
discovery.py - pull candidate LinkedIn-post angles from live sources
instead of inventing one when the user gives a bare topic.

Three sources, each read-only, no auth required:

  1. GOOGLE NEWS   one RSS query per entry in sources.json's
                    google_news_queries (or a single --topic override).
  2. AWS WHAT'S NEW the AWS "recent" RSS feed, filtered to items whose
                    title/summary overlaps the topic keywords.
  3. GITHUB RELEASES the last --days of releases for each repo in
                    sources.json's github_repos, via the public,
                    unauthenticated REST API (60 req/hr rate limit).

Every candidate is scored by keyword overlap against --topic (plus, if a
voice.md path is given, keywords from its "My positions" and "Focus areas"
sections) and by recency, then printed newest-and-most-relevant first. This is a
ranking heuristic, not a relevance model - skim the list, don't trust it
blindly.

Usage
  python3 discovery.py --topic "kubernetes autoscaling" --days 14
  python3 discovery.py --days 7 --limit 5 --json
  python3 discovery.py --topic "agentic AI" --voice ~/.claude/linkedin/voice.md
"""

import argparse
import html
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import voice

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, "sources.json")
UA = "genai-linkedin-composer/1.0 (+https://github.com/)"
TIMEOUT = 12


def load_sources(path=SOURCES):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        if not isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
            raise
        # This Python has no CA bundle (common on python.org macOS builds).
        # Retry through system curl, which uses the OS trust store. Verification stays on.
        out = subprocess.run(["curl", "-fsSL", "--max-time", str(TIMEOUT), "-A", UA, url],
                             capture_output=True)
        if out.returncode != 0:
            raise RuntimeError(f"curl fallback failed ({out.returncode}): {out.stderr.decode()[:120]}")
        return out.stdout


def parse_rss(raw):
    """Minimal RSS 2.0 / Atom item extractor - title, link, date, summary."""
    items = []
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return items
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title = (it.findtext("title") or it.findtext("a:title", namespaces=ns) or "").strip()
        link_el = it.find("link")
        if link_el is not None and link_el.text:
            link = link_el.text.strip()
        elif link_el is not None:
            link = link_el.get("href", "")
        else:
            link = ""
        date_raw = (it.findtext("pubDate") or it.findtext("a:published", namespaces=ns)
                    or it.findtext("a:updated", namespaces=ns) or "")
        summary = (it.findtext("description") or it.findtext("a:summary", namespaces=ns) or "")
        summary = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", summary))).strip()
        items.append({"title": title, "link": link, "date_raw": date_raw, "summary": summary[:300]})
    return items


def parse_date(date_raw):
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            d = datetime.strptime(date_raw, fmt)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d
        except ValueError:
            continue
    return None


def pull_google_news(query, days):
    q = urllib.parse.quote(f"{query} when:{days}d")
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    try:
        raw = fetch(url)
    except Exception as e:
        return [], str(e)
    items = parse_rss(raw)
    for it in items:
        it["source"] = f"Google News: {query}"
    return items, None


def pull_aws_whats_new(feed_url, keywords, days):
    try:
        raw = fetch(feed_url)
    except Exception as e:
        return [], str(e)
    items = parse_rss(raw)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for it in items:
        d = parse_date(it["date_raw"])
        if d and d < cutoff:
            continue
        blob = (it["title"] + " " + it["summary"]).lower()
        if keywords and not any(k.lower() in blob for k in keywords):
            continue
        it["source"] = "AWS What's New"
        out.append(it)
    return out, None


def pull_github_releases(repo, days):
    url = f"https://api.github.com/repos/{repo}/releases?per_page=10"
    try:
        raw = fetch(url)
        data = json.loads(raw)
    except Exception as e:
        return [], str(e)
    if not isinstance(data, list):
        msg = data.get("message", "unexpected response") if isinstance(data, dict) else "unexpected response"
        return [], msg
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for r in data:
        published = r.get("published_at") or r.get("created_at")
        if not published:
            continue
        d = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if d < cutoff:
            continue
        out.append({
            "title": f"{repo} {r.get('name') or r.get('tag_name')}",
            "link": r.get("html_url", ""),
            "date_raw": published,
            "summary": (r.get("body") or "")[:300].replace("\r\n", " ").replace("\n", " "),
            "source": f"GitHub releases: {repo}",
        })
    return out, None


def score(item, keywords):
    blob = (item["title"] + " " + item["summary"]).lower()
    kw_hits = sum(1 for k in keywords if k.lower() in blob)
    d = parse_date(item["date_raw"])
    age_days = (datetime.now(timezone.utc) - d).days if d else 99
    recency = max(0, 30 - age_days) / 30
    primary = 0.5 if item.get("source", "").startswith(("AWS", "GitHub")) else 0.0
    return kw_hits * 2 + recency + primary


def main():
    ap = argparse.ArgumentParser(description="Pull candidate LinkedIn-post angles from live sources.")
    ap.add_argument("--topic", help="focus query; also used for keyword scoring")
    ap.add_argument("--voice", help="path to voice.md - 'My positions' and 'Focus areas' add scoring keywords")
    ap.add_argument("--days", type=int, default=14, help="lookback window (default 14)")
    ap.add_argument("--limit", type=int, default=8, help="max candidates to show (default 8)")
    ap.add_argument("--sources", default=SOURCES, help="path to sources.json")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cfg = load_sources(args.sources)
    keywords = []
    if args.voice:
        if not os.path.exists(voice.resolve(args.voice)):
            sys.exit(f"error: --voice file not found: {args.voice}")
        for line in voice.positions(args.voice) + voice.focus_areas(args.voice):
            keywords.extend(re.findall(r"[A-Za-z][A-Za-z\-]{3,}", line))
    if args.topic:
        keywords.extend(re.findall(r"[A-Za-z][A-Za-z\-]{2,}", args.topic))
    queries = [args.topic] if args.topic else cfg["google_news_queries"]

    candidates, errors = [], []

    for q in queries:
        items, err = pull_google_news(q, args.days)
        if err:
            errors.append(f"Google News ({q}): {err}")
        candidates.extend(items)

    items, err = pull_aws_whats_new(cfg["aws_whats_new_feed"], keywords, args.days)
    if err:
        errors.append(f"AWS What's New: {err}")
    candidates.extend(items)

    for repo in cfg["github_repos"]:
        items, err = pull_github_releases(repo, args.days)
        if err:
            errors.append(f"GitHub ({repo}): {err}")
        candidates.extend(items)

    for c in candidates:
        c["score"] = round(score(c, keywords), 2)
    candidates.sort(key=lambda c: c["score"], reverse=True)
    candidates = candidates[: args.limit]

    if args.json:
        print(json.dumps({"candidates": candidates, "errors": errors}, indent=2, ensure_ascii=False))
        return

    if not candidates:
        print("No candidates found in the window. Widen --days, add a --topic, or check --sources.")
    for i, c in enumerate(candidates, 1):
        print(f"\n{i}. [{c['score']:.1f}] {c['title']}")
        print(f"   {c['source']}  |  {c['date_raw']}")
        if c["summary"]:
            print(f"   {c['summary'][:180]}{'...' if len(c['summary']) > 180 else ''}")
        if c["link"]:
            print(f"   {c['link']}")
    if errors:
        print("\n--- source errors (network or rate limit; results above are partial) ---", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
