#!/usr/bin/env python3
"""PostToolUse hook: validate /series-log.md after any Write/Edit to it.

series-log.md is the only cross-session continuity mechanism for the
youtube-episode skill (episode numbering + duplicate-topic detection).
This must fail loudly on corruption rather than let a bad file pass
silently into the next session.
"""
import json
import re
import sys

EXPECTED_COLUMNS = 9  # Episode | Slug | Title | Format | Duration Pref | Slot Rule Applied | Video | Date Logged | Topic


def fail(message: str) -> None:
    sys.stderr.write(f"series-log.md validation FAILED: {message}\n")
    sys.exit(2)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Nothing we can validate without hook input; don't block on this.
        sys.exit(0)

    file_path = (
        payload.get("tool_input", {}).get("file_path", "")
        or payload.get("tool_response", {}).get("filePath", "")
    )
    if not file_path.endswith("series-log.md"):
        sys.exit(0)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        fail(f"could not read {file_path}: {e}")
        return

    lines = [l for l in text.splitlines() if l.strip()]
    table_lines = [l for l in lines if l.strip().startswith("|")]

    if len(table_lines) < 1:
        fail("no markdown table found (missing header row)")
        return

    header = table_lines[0]
    if "Episode" not in header:
        fail("header row missing or malformed (expected an 'Episode' column)")
        return

    # Second table line is the '---' separator row, if present.
    data_rows = table_lines[1:]
    if data_rows and re.match(r"^\|[\s:-]+\|$", data_rows[0].replace("-", "-")):
        data_rows = data_rows[1:]
    elif data_rows and set(data_rows[0].replace("|", "").strip()) <= {"-", " ", ":"}:
        data_rows = data_rows[1:]

    seen_episodes = set()
    for i, row in enumerate(data_rows, start=1):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) != EXPECTED_COLUMNS:
            fail(
                f"row {i} has {len(cells)} columns, expected {EXPECTED_COLUMNS}: {row!r}"
            )
            return
        episode = cells[0]
        if not re.match(r"^\d{2,}$", episode):
            fail(f"row {i} has a non-numeric/malformed episode number: {episode!r}")
            return
        if episode in seen_episodes:
            fail(f"duplicate episode number {episode!r} (row {i})")
            return
        seen_episodes.add(episode)

    sys.exit(0)


if __name__ == "__main__":
    main()
