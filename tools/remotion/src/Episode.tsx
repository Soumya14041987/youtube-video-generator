import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

// ---- data contract (written by tools/dual_host/render_remotion.py) -------------------------------------------
export type Line = {start: number; end: number; speaker: string; text: string}; // seconds, relative to the scene start
export type SceneData = {
  n: number;
  start: number; // seconds from the start of the video
  end: number;
  title: string;
  lines: Line[];
  scene: Record<string, any>; // {type: 'title' | 'bullets' | 'code' | 'terminal' | 'diagram' | 'compare' | 'quiz' | 'takeaways' | 'end', ...}
};
export type EpisodeProps = {
  fps: number;
  width: number;
  height: number;
  totalSeconds: number;
  audio: string; // file inside public/, for example current/audio.wav
  badge: string;
  follow: {label: string; handle: string}[];
  quiz: {countdownStart: number; revealAt: number; seconds: number} | null; // absolute seconds
  scenes: SceneData[];
};

// ---- look ---------------------------------------------------------------------------------------------------
const C = {
  bg: '#0d1117', panel: '#141b26', line: '#8b949e', white: '#e6edf3', gray: '#8b949e', green: '#39d353', dkGreen: '#0f2d19',
  red: '#f85149', dkRed: '#321212', yellow: '#ffd700', blue: '#58a6ff', dkBlue: '#122038', purple: '#bc8cff', dkPurple: '#26193c',
  orange: '#ffa657', dkOrange: '#342210', code: '#0a0e14',
};
const ACCENTS: Record<string, [string, string]> = {
  blue: [C.blue, C.dkBlue], green: [C.green, C.dkGreen], orange: [C.orange, C.dkOrange], purple: [C.purple, C.dkPurple],
  red: [C.red, C.dkRed], yellow: [C.yellow, '#2d280c'],
};
const accent = (name?: string): [string, string] => ACCENTS[name ?? 'blue'] ?? ACCENTS.blue;
const SANS = 'Helvetica Neue, Helvetica, Arial, sans-serif';
const MONO = 'Menlo, Consolas, "DejaVu Sans Mono", monospace';

// ---- helpers ------------------------------------------------------------------------------------------------
const useT = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return frame / fps;
};
const appear = (t: number, at: number, dur = 0.45) =>
  interpolate(t, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
const pop = (t: number, at: number): React.CSSProperties => {
  const p = appear(t, at);
  return {opacity: p, transform: `translateY(${(1 - p) * 18}px)`};
};
const Box: React.FC<{color: string; fill: string; style?: React.CSSProperties; children?: React.ReactNode}> = ({color, fill, style, children}) => (
  <div style={{border: `3px solid ${color}`, background: fill, borderRadius: 16, boxSizing: 'border-box', ...style}}>{children}</div>
);

const Header: React.FC<{n: number; title: string}> = ({n, title}) => (
  <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 54, background: '#121a26', borderBottom: `3px solid ${C.green}`, display: 'flex', alignItems: 'center', fontFamily: SANS}}>
    <span style={{color: C.green, fontSize: 24, fontWeight: 700, margin: '0 14px 0 18px'}}>{n}.</span>
    <span style={{color: C.white, fontSize: 24, fontWeight: 700}}>{title}</span>
  </div>
);

const Banner: React.FC<{text: string; color?: string; at?: number}> = ({text, color = 'green', at = 0.4}) => {
  const t = useT();
  const [c, f] = accent(color);
  return (
    <Box color={c} fill={f} style={{position: 'absolute', left: 60, right: 60, bottom: 40, height: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', ...pop(t, at)}}>
      <span style={{color: c, fontSize: 26, fontWeight: 700, fontFamily: SANS}}>{text}</span>
    </Box>
  );
};

// ---- scenes -------------------------------------------------------------------------------------------------
const TitleScene: React.FC<{s: Record<string, any>; badge: string}> = ({s, badge}) => {
  const t = useT();
  const colors = [C.yellow, C.green, C.white];
  const lines: string[] = s.headline ?? [];
  return (
    <AbsoluteFill style={{alignItems: 'center', fontFamily: SANS}}>
      <div style={{marginTop: 70, background: C.red, color: C.white, fontWeight: 700, fontSize: 26, padding: '10px 36px', borderRadius: 24, ...pop(t, 0)}}>{badge}</div>
      <div style={{marginTop: 28, textAlign: 'center'}}>
        {lines.map((l, i) => (
          <div key={i} style={{color: colors[i % 3], fontSize: i === 0 ? 120 : 96, fontWeight: 800, lineHeight: 1.1, ...pop(t, 0.2 + i * 0.25)}}>{l}</div>
        ))}
      </div>
      {s.subtitle && <div style={{marginTop: 34, color: C.white, fontSize: 38, fontWeight: 700, ...pop(t, 0.9)}}>{s.subtitle}</div>}
      {s.tag && (
        <Box color={C.green} fill={C.dkGreen} style={{marginTop: 34, padding: '12px 40px', ...pop(t, 1.2)}}>
          <span style={{color: C.green, fontSize: 32, fontWeight: 700}}>{s.tag}</span>
        </Box>
      )}
    </AbsoluteFill>
  );
};

const BulletsScene: React.FC<{s: Record<string, any>}> = ({s}) => {
  const t = useT();
  const items: any[] = s.items ?? [];
  const cols = items.length > 4 ? 2 : 1;
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      <div style={{position: 'absolute', top: 90, left: 50, right: 50, display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 18}}>
        {items.map((raw, i) => {
          const it: Record<string, any> = typeof raw === 'string' ? {head: raw} : raw;
          const [c, f] = accent(it.color ?? ['blue', 'green', 'orange', 'purple', 'red', 'yellow'][i % 6]);
          return (
            <Box key={i} color={c} fill={f} style={{padding: '16px 22px', ...pop(t, it.at ?? i * 0.6)}}>
              <div style={{color: c, fontSize: 30, fontWeight: 700}}>{it.head}</div>
              {it.text && <div style={{color: C.white, fontSize: 24, marginTop: 8, lineHeight: 1.3}}>{it.text}</div>}
            </Box>
          );
        })}
      </div>
      {s.banner && <Banner text={s.banner} color={s.bannerColor ?? 'green'} at={s.bannerAt ?? 1} />}
    </AbsoluteFill>
  );
};

const CodeBlock: React.FC<{code: string; at: number[]; highlight?: number[]; size?: number; width?: number}> = ({code, at, highlight = [], size = 24, width = 700}) => {
  const t = useT();
  const lines = code.split('\n');
  const longest = Math.max(...lines.map((l) => l.length), 1);
  const fit = Math.floor((width - 56) / (longest * 0.62)); // shrink long lines so they stay inside the panel
  return (
    <div style={{background: C.code, border: `2px solid ${C.line}`, borderRadius: 12, padding: '16px 20px', fontFamily: MONO, fontSize: Math.min(size, fit), lineHeight: 1.45, color: C.white, whiteSpace: 'pre'}}>
      {lines.map((ln, i) => {
        const hl = highlight.includes(i + 1);
        return (
          <div key={i} style={{opacity: appear(t, at[i] ?? 0, 0.3), background: hl ? 'rgba(255,215,0,0.14)' : 'transparent', marginLeft: -8, paddingLeft: 8, color: ln.trim().startsWith('#') ? C.gray : C.white}}>
            {ln || ' '}
          </div>
        );
      })}
    </div>
  );
};

const CodeScene: React.FC<{s: Record<string, any>}> = ({s}) => {
  const t = useT();
  const code: string = s.code ?? '';
  const n = code.split('\n').length;
  const first = s.codeAt ?? 0;
  const spread = s.codeSpan ?? Math.min(4, n * 0.3);
  const at = Array.from({length: n}, (_, i) => first + (n > 1 ? (i / (n - 1)) * spread : 0));
  const notes: any[] = s.notes ?? [];
  const codeW = notes.length ? 700 : 1160;
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      <div style={{position: 'absolute', top: 88, left: 40, width: codeW}}>
        <CodeBlock code={code} at={at} highlight={s.highlight} size={s.size ?? 24} width={codeW} />
      </div>
      {notes.length > 0 && (
        <div style={{position: 'absolute', top: 88, left: 770, right: 40, display: 'flex', flexDirection: 'column', gap: 16}}>
          {notes.map((nt, i) => {
            const [c, f] = accent(nt.color ?? ['blue', 'orange', 'green', 'purple'][i % 4]);
            return (
              <Box key={i} color={c} fill={f} style={{padding: '12px 20px', ...pop(t, nt.at ?? 1 + i)}}>
                <div style={{color: c, fontSize: 28, fontWeight: 700}}>{nt.head}</div>
                <div style={{color: C.white, fontSize: 22, marginTop: 6, lineHeight: 1.3}}>{nt.text}</div>
              </Box>
            );
          })}
        </div>
      )}
      {s.banner && <Banner text={s.banner} color={s.bannerColor ?? 'green'} at={s.bannerAt ?? 2} />}
    </AbsoluteFill>
  );
};

const TerminalScene: React.FC<{s: Record<string, any>}> = ({s}) => {
  const t = useT();
  const cmds: any[] = s.commands ?? [];
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      <div style={{position: 'absolute', top: 88, left: 40, width: s.hints ? 700 : 1160, background: C.code, border: `2px solid ${C.green}`, borderRadius: 12, padding: '18px 22px', fontFamily: MONO, fontSize: s.size ?? 28, lineHeight: 1.55}}>
        {cmds.map((c, i) => {
          const at = c.at ?? i * 0.8;
          const chars = Math.floor(interpolate(t, [at, at + 0.7], [0, c.text.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
          const comment = c.text.startsWith('#');
          return (
            <div key={i} style={{opacity: t >= at ? 1 : 0, color: comment ? C.gray : C.white}}>
              {!comment && <span style={{color: C.green}}>$ </span>}
              {c.text.slice(0, chars)}
            </div>
          );
        })}
      </div>
      {s.hints && (
        <div style={{position: 'absolute', top: 88, left: 770, right: 40}}>
          <Box color={C.blue} fill={C.dkBlue} style={{padding: '14px 22px', ...pop(t, 0.3)}}>
            <div style={{color: C.blue, fontSize: 28, fontWeight: 700, textAlign: 'center'}}>{s.hintsTitle ?? 'What each line does'}</div>
            {(s.hints as any[]).map((h, i) => (
              <div key={i} style={{display: 'flex', marginTop: 12, ...pop(t, h.at ?? 1 + i * 0.6)}}>
                <span style={{fontFamily: MONO, color: C.yellow, fontSize: 24, width: 190}}>{h.cmd}</span>
                <span style={{color: C.white, fontSize: 24}}>{h.text}</span>
              </div>
            ))}
          </Box>
        </div>
      )}
      {s.banner && <Banner text={s.banner} color={s.bannerColor ?? 'green'} at={s.bannerAt ?? 2} />}
    </AbsoluteFill>
  );
};

const DiagramScene: React.FC<{s: Record<string, any>}> = ({s}) => {
  const t = useT();
  const nodes: any[] = s.nodes ?? [];
  const n = nodes.length || 1;
  const gap = 70;
  const w = Math.min(300, (1180 - gap * (n - 1)) / n);
  const x0 = (1280 - (w * n + gap * (n - 1))) / 2;
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      {nodes.map((nd, i) => {
        const [c, f] = accent(nd.color ?? ['blue', 'green', 'orange', 'purple'][i % 4]);
        const x = x0 + i * (w + gap);
        const at = nd.at ?? i * 0.9;
        return (
          <React.Fragment key={i}>
            <Box color={c} fill={f} style={{position: 'absolute', left: x, top: 190, width: w, height: 220, padding: 16, textAlign: 'center', ...pop(t, at)}}>
              <div style={{color: c, fontSize: 34, fontWeight: 800, marginTop: 28}}>{nd.label}</div>
              {nd.sub && <div style={{color: C.white, fontSize: 22, marginTop: 14, lineHeight: 1.3}}>{nd.sub}</div>}
            </Box>
            {i < n - 1 && (
              <div style={{position: 'absolute', left: x + w + 8, top: 282, width: gap - 16, color: C.yellow, fontSize: 48, textAlign: 'center', opacity: appear(t, at + 0.5)}}>{'→'}</div>
            )}
            {nd.caption && (
              <div style={{position: 'absolute', left: x, top: 430, width: w, textAlign: 'center', color: C.gray, fontSize: 22, ...pop(t, at + 0.3)}}>{nd.caption}</div>
            )}
          </React.Fragment>
        );
      })}
      {s.banner && <Banner text={s.banner} color={s.bannerColor ?? 'yellow'} at={s.bannerAt ?? n * 0.9} />}
    </AbsoluteFill>
  );
};

const CompareScene: React.FC<{s: Record<string, any>}> = ({s}) => {
  const t = useT();
  const side = (d: any, left: boolean) => {
    const [c, f] = accent(d.color ?? (left ? 'blue' : 'orange'));
    return (
      <Box color={c} fill={f} style={{position: 'absolute', top: 95, [left ? 'left' : 'right']: 40, width: 585, height: 400, padding: '18px 26px', ...pop(t, d.at ?? (left ? 0.2 : 1.2))}}>
        <div style={{color: c, fontSize: 40, fontWeight: 800, textAlign: 'center'}}>{d.head}</div>
        <div style={{marginTop: 16}}>
          {(d.items ?? []).map((it: string, i: number) => (
            <div key={i} style={{color: C.white, fontSize: 26, marginTop: 12, lineHeight: 1.3, ...pop(t, (d.at ?? (left ? 0.2 : 1.2)) + 0.4 + i * 0.5)}}>{'•'} {it}</div>
          ))}
        </div>
        {d.code && (
          <div style={{position: 'absolute', left: 26, right: 26, bottom: 20, background: C.code, border: `2px solid ${c}`, borderRadius: 10, padding: '10px 14px', fontFamily: MONO, fontSize: 21, color: C.white, whiteSpace: 'pre'}}>{d.code}</div>
        )}
      </Box>
    );
  };
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      {side(s.left ?? {}, true)}
      {side(s.right ?? {}, false)}
      {s.banner && <Banner text={s.banner} color={s.bannerColor ?? 'yellow'} at={s.bannerAt ?? 3} />}
    </AbsoluteFill>
  );
};

const QuizScene: React.FC<{s: Record<string, any>; quiz: EpisodeProps['quiz']; absStart: number}> = ({s, quiz, absStart}) => {
  const t = useT();
  const abs = absStart + t;
  const options: string[] = s.options ?? [];
  const revealed = quiz ? abs >= quiz.revealAt : false;
  const counting = quiz ? abs >= quiz.countdownStart && abs < quiz.revealAt : false;
  const left = quiz ? Math.max(0, Math.ceil(quiz.revealAt - abs)) : 0;
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      <Box color={C.blue} fill="#19233a" style={{position: 'absolute', top: 70, left: 60, right: 60, height: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8}}>
        <span style={{color: C.blue, fontSize: 24, fontWeight: 700}}>{s.kicker ?? 'Exam Checkpoint'}</span>
      </Box>
      <Box color={C.purple} fill={C.dkPurple} style={{position: 'absolute', top: 136, left: 60, width: 64, height: 68, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8}}>
        <span style={{color: C.purple, fontSize: 42, fontWeight: 800}}>Q</span>
      </Box>
      <div style={{position: 'absolute', top: 140, left: 146, right: 60, color: C.white, fontSize: 28, fontWeight: 700, lineHeight: 1.35}}>{s.question}</div>
      {options.map((o, i) => {
        const ok = i === s.correct;
        const hot = revealed && ok;
        const dim = revealed && !ok;
        return (
          <div key={i} style={{position: 'absolute', top: 262 + i * 70, left: 60, right: 60, height: 58, boxSizing: 'border-box', borderRadius: 10, border: `${hot ? 4 : 1}px solid ${hot ? C.green : dim ? '#3c424c' : C.line}`, background: hot ? C.dkGreen : C.panel, display: 'flex', alignItems: 'center', padding: '0 28px', ...pop(t, 0.6 + i * 0.3)}}>
            <span style={{fontSize: 26, fontWeight: hot ? 700 : 400, color: hot ? C.green : dim ? '#78808a' : C.white, width: 52}}>{String.fromCharCode(65 + i)}</span>
            <span style={{fontSize: 26, fontWeight: hot ? 700 : 400, color: hot ? C.green : dim ? '#78808a' : C.white}}>{o}</span>
            {hot && <span style={{marginLeft: 'auto', color: C.green, fontSize: 24, fontWeight: 700}}>Correct Answer</span>}
          </div>
        );
      })}
      <Box color={revealed ? C.green : C.yellow} fill={revealed ? '#0f1e14' : C.panel} style={{position: 'absolute', top: 552, left: 60, right: 60, height: 140, padding: '16px 30px', borderRadius: 10, borderWidth: 2}}>
        {revealed ? (
          <>
            <div style={{color: C.green, fontSize: 26, fontWeight: 700}}>Why {String.fromCharCode(65 + (s.correct ?? 0))} is correct</div>
            <div style={{color: C.white, fontSize: 22, marginTop: 10, lineHeight: 1.35}}>{s.explanation}</div>
          </>
        ) : (
          <div style={{display: 'flex', alignItems: 'center', height: '100%'}}>
            <div style={{flex: 1}}>
              <div style={{color: C.yellow, fontSize: 30, fontWeight: 700}}>Pause and think</div>
              <div style={{color: C.white, fontSize: 22, marginTop: 8}}>Which option would you choose? The answer is revealed when the timer ends.</div>
            </div>
            {counting && (
              <div style={{textAlign: 'center', width: 150}}>
                <div style={{color: C.yellow, fontSize: 78, fontWeight: 800, lineHeight: 1}}>{left}</div>
                <div style={{color: C.white, fontSize: 18}}>seconds</div>
              </div>
            )}
          </div>
        )}
      </Box>
    </AbsoluteFill>
  );
};

const TakeawaysScene: React.FC<{s: Record<string, any>}> = ({s}) => {
  const t = useT();
  const items: any[] = s.items ?? [];
  return (
    <AbsoluteFill style={{fontFamily: SANS}}>
      {items.map((raw, i) => {
        const it: Record<string, any> = typeof raw === 'string' ? {text: raw} : raw; // a plain string has a built-in .at function, so wrap it
        const [c] = accent(it.color ?? ['blue', 'green', 'orange', 'red', 'yellow', 'green'][i % 6]);
        const text = it.text;
        return (
          <div key={i} style={{position: 'absolute', left: 60, right: 60, top: 85 + i * 92, height: 78, border: `2px solid ${c}`, borderRadius: 12, background: C.panel, display: 'flex', alignItems: 'center', ...pop(t, (it.at ?? i * 0.7))}}>
            <div style={{marginLeft: 18, width: 54, height: 54, borderRadius: 10, background: c, color: C.bg, fontSize: 34, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{i + 1}</div>
            <div style={{marginLeft: 28, color: C.white, fontSize: 28, fontWeight: 700}}>{text}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const EndScene: React.FC<{s: Record<string, any>; follow: EpisodeProps['follow']; name?: string}> = ({s, follow}) => {
  const t = useT();
  return (
    <AbsoluteFill style={{alignItems: 'center', fontFamily: SANS}}>
      <div style={{marginTop: 34, color: C.white, fontSize: 54, fontWeight: 800}}>{s.thanks ?? 'Thanks for watching'}</div>
      {s.nextTitle && (
        <Box color={C.green} fill={C.dkGreen} style={{marginTop: 24, width: 600, padding: '14px 0', textAlign: 'center', ...pop(t, 0.4)}}>
          <div style={{color: C.green, fontSize: 36, fontWeight: 700}}>{s.nextLabel ?? 'Next'}</div>
          <div style={{color: C.white, fontSize: 34, fontWeight: 700, marginTop: 6}}>{s.nextTitle}</div>
        </Box>
      )}
      <div style={{display: 'flex', gap: 60, marginTop: 36, ...pop(t, 0.9)}}>
        {[['Like', C.blue], ['Comment', C.purple], ['Subscribe', C.red]].map(([l, c]) => (
          <div key={l} style={{width: 300, height: 80, borderRadius: 40, background: c as string, color: C.white, fontSize: 32, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{l}</div>
        ))}
      </div>
      {follow.length > 0 && (
        <>
          <div style={{marginTop: 34, color: C.yellow, fontSize: 36, fontWeight: 700, ...pop(t, 1.4)}}>{s.followTitle ?? 'Follow to reach out'}</div>
          <div style={{display: 'flex', gap: 30, marginTop: 20, ...pop(t, 1.7)}}>
            {follow.slice(0, 3).map((f, i) => {
              const c = [C.blue, C.green, C.purple][i];
              return (
                <Box key={i} color={c} fill={C.panel} style={{width: 370, padding: '14px 0', textAlign: 'center'}}>
                  <div style={{color: c, fontSize: 32, fontWeight: 700}}>{f.label}</div>
                  <div style={{color: C.white, fontSize: 22, marginTop: 8}}>{f.handle}</div>
                </Box>
              );
            })}
          </div>
        </>
      )}
      <div style={{marginTop: 30, color: C.gray, fontSize: 26, ...pop(t, 2.2)}}>Links are in the description</div>
      {s.cta && <div style={{marginTop: 10, color: C.white, fontSize: 28, fontWeight: 700, ...pop(t, 2.4)}}>{s.cta}</div>}
    </AbsoluteFill>
  );
};

// ---- episode ------------------------------------------------------------------------------------------------
export const Episode: React.FC<EpisodeProps> = (props) => {
  const {fps, width, scenes, audio, badge, follow, quiz} = props;
  const k = width / 1280;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      <div style={{width: 1280, height: 720, transform: `scale(${k})`, transformOrigin: '0 0', position: 'relative'}}>
        {scenes.map((sc) => {
          const from = Math.round(sc.start * fps);
          const dur = Math.max(1, Math.round((sc.end - sc.start) * fps));
          const type = sc.scene?.type ?? 'bullets';
          const showHeader = !['title', 'end', 'quiz'].includes(type);
          return (
            <Sequence key={sc.n} from={from} durationInFrames={dur}>
              <AbsoluteFill>
                {showHeader && <Header n={sc.n} title={sc.title} />}
                {type === 'title' && <TitleScene s={sc.scene} badge={badge} />}
                {type === 'bullets' && <BulletsScene s={sc.scene} />}
                {type === 'code' && <CodeScene s={sc.scene} />}
                {type === 'terminal' && <TerminalScene s={sc.scene} />}
                {type === 'diagram' && <DiagramScene s={sc.scene} />}
                {type === 'compare' && <CompareScene s={sc.scene} />}
                {type === 'quiz' && <QuizScene s={sc.scene} quiz={quiz} absStart={sc.start} />}
                {type === 'takeaways' && <TakeawaysScene s={sc.scene} />}
                {type === 'end' && <EndScene s={sc.scene} follow={follow} />}
              </AbsoluteFill>
            </Sequence>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
