import React, {useMemo} from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import katex from 'katex';

const C = {
  ink: '#171719',
  muted: '#676774',
  line: 'rgba(64,66,84,0.16)',
  blue: '#5367f0',
  blueSoft: '#dce3ff',
  teal: '#1f9d84',
  amber: '#c78b19',
  rose: '#c95c72',
  violet: '#7c6ff0',
  paper: 'rgba(255,255,255,0.84)',
};

const ACTS = [
  {start: 0, duration: 1092, kicker: '01 / Contagion', title: 'Risk moves before prices do'},
  {start: 1092, duration: 732, kicker: '02 / Embedding', title: 'A sentence becomes a coordinate'},
  {start: 1824, duration: 888, kicker: '03 / Taxonomy', title: 'The map learns new risk language'},
  {start: 2712, duration: 900, kicker: '04 / ST-GAT', title: 'Volatility flows through topology'},
  {start: 3612, duration: 732, kicker: '05 / Alpha', title: 'The graph becomes a portfolio signal'},
];

const INTRO_FRAMES = 48;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const ease = Easing.bezier(0.22, 0.8, 0.24, 1);
const t = (frame, start, end) => interpolate(frame, [start, end], [0, 1], clamp);
const et = (frame, start, end) => ease(t(frame, start, end));
const fadeIn = (frame, start, len = 20) => t(frame, start, start + len);
const fadeOut = (frame, end, len = 20) => interpolate(frame, [end - len, end], [1, 0], clamp);
const segment = (frame, start, end, len = 20) => fadeIn(frame, start, len) * fadeOut(frame, end, len);
const mix = (a, b, p) => a + (b - a) * p;
const wave = (frame, speed = 1, phase = 0) => Math.sin(frame * speed + phase);
const toPoints = (pts) => pts.map((pt) => pt.join(',')).join(' ');
const rand = (seed) => {
  const n = Math.sin(seed * 127.1) * 43758.5453123;
  return n - Math.floor(n);
};

export const QuantNlpRiskVideo = () => {
  const frame = useCurrentFrame();
  const {width, height, fps, durationInFrames} = useVideoConfig();
  const musicEnd = durationInFrames - fps;
  const isIntro = frame < INTRO_FRAMES;
  const contentFrame = Math.max(0, frame - INTRO_FRAMES);
  const actIndex = Math.min(
    ACTS.length - 1,
    Math.max(0, ACTS.findIndex((act) => contentFrame >= act.start && contentFrame < act.start + act.duration)),
  );
  const safeIndex = actIndex === -1 ? ACTS.length - 1 : actIndex;
  const act = ACTS[safeIndex];
  const localFrame = contentFrame - act.start;

  return (
    <AbsoluteFill className="video-root">
      <Audio
        src={staticFile('background_music.mp3')}
        trimAfter={musicEnd}
        volume={(f) => interpolate(f, [musicEnd - fps * 5, musicEnd], [1, 0], clamp)}
      />
      <Background frame={frame} />
      {isIntro ? <FrontPage frame={frame} /> : null}
      {!isIntro && safeIndex === 0 ? <Act1 frame={localFrame} /> : null}
      {!isIntro && safeIndex === 1 ? <Act2 frame={localFrame} /> : null}
      {!isIntro && safeIndex === 2 ? <Act3 frame={localFrame} /> : null}
      {!isIntro && safeIndex === 3 ? <Act4 frame={localFrame} /> : null}
      {!isIntro && safeIndex === 4 ? <Act5 frame={localFrame} /> : null}
      {!isIntro ? <Header act={act} frame={localFrame} opacity={safeIndex === 4 ? fadeOut(localFrame, 656, 36) : 1} /> : null}
      <LogoStrip />
      {isIntro ? <div className="wipe" style={{opacity: interpolate(frame, [INTRO_FRAMES - 16, INTRO_FRAMES - 1], [0, 1], clamp)}} /> : null}
      <TransitionVeil frame={contentFrame} width={width} height={height} />
    </AbsoluteFill>
  );
};

const Background = ({frame}) => {
  const sweep = interpolate((frame % 260) / 260, [0, 1], [-260, 1540]);
  const band = 36 * wave(frame, 0.006);
  return (
    <AbsoluteFill>
      <AbsoluteFill className="grid-bg" style={{opacity: 0.86}} />
      <div
        style={{
          position: 'absolute',
          left: -260 + band,
          top: 130,
          width: 1620,
          height: 430,
          background:
            'linear-gradient(90deg, rgba(83,103,240,0), rgba(83,103,240,0.12), rgba(31,157,132,0.12), rgba(199,139,25,0.09), rgba(83,103,240,0))',
          filter: 'blur(34px)',
          transform: 'rotate(-7deg)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: sweep,
          top: 0,
          width: 150,
          height: 720,
          background:
            'linear-gradient(90deg, rgba(255,255,255,0), rgba(83,103,240,0.07), rgba(255,255,255,0))',
          transform: 'skewX(-14deg)',
        }}
      />
    </AbsoluteFill>
  );
};

const FrontPage = ({frame}) => {
  const opacity = fadeOut(frame, INTRO_FRAMES, 14);
  const titleY = interpolate(frame, [0, INTRO_FRAMES - 1], [10, -2], clamp);
  const accent = 0.5 + 0.5 * wave(frame, 0.06);
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 10,
        opacity,
        color: C.ink,
        pointerEvents: 'none',
      }}
    >
      <Svg>
        <circle cx="207" cy="210" fill={C.blue} opacity="0.08" r={110 + 8 * accent} />
        <circle cx="1018" cy="515" fill={C.teal} opacity="0.08" r={136 - 8 * accent} />
        <path
          d="M184 502 C 382 374, 521 454, 698 330 S 978 178, 1112 252"
          fill="none"
          opacity="0.22"
          stroke={C.amber}
          strokeDasharray="8 12"
          strokeLinecap="round"
          strokeWidth="3"
        />
        {[0, 1, 2, 3, 4].map((i) => (
          <circle
            cx={250 + i * 190}
            cy={472 - Math.sin(frame * 0.035 + i) * 18}
            fill={[C.blue, C.teal, C.amber, C.rose, C.violet][i]}
            key={i}
            opacity="0.13"
            r={18 + i * 2}
          />
        ))}
      </Svg>
      <div style={{position: 'absolute', left: 78, top: 126, width: 820, transform: `translateY(${titleY}px)`}}>
        <div className="kicker" style={{fontSize: 25}}>Quantitative Finance NLP Research</div>
        <h1
          style={{
            margin: '12px 0 0',
            fontSize: 58,
            lineHeight: 1.12,
            letterSpacing: 0,
            fontWeight: 400,
            maxWidth: 820,
          }}
        >
          The Topology of Risk:
          <br />
          ST-GAT and Dynamic NLP Risk Networks
        </h1>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 86,
          right: 86,
          bottom: 74,
          display: 'grid',
          gridTemplateColumns: '1.5fr 0.82fr 0.82fr',
          gap: 18,
          alignItems: 'stretch',
        }}
      >
        <TitleCredit label="Research team">
          CHAN Ho Lam Myles&nbsp;&nbsp;|&nbsp;&nbsp;CHOI Man Hou&nbsp;&nbsp;|&nbsp;&nbsp;TSOI Ching Yi
          <div style={{fontSize: 19, color: C.muted, marginTop: 5}}>Dual Degree Program, HKUST</div>
        </TitleCredit>
        <TitleCredit label="Supervisor">
          Dr. Jiang Wei
          <div style={{fontSize: 18, color: C.muted, marginTop: 5}}>IEDA Department, HKUST</div>
        </TitleCredit>
        <TitleCredit label="Industry partner">
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <Img src={staticFile('worldquant_logo.jpg')} style={{width: 42, height: 42, objectFit: 'contain', borderRadius: 6}} />
            <span>WorldQuant</span>
          </div>
        </TitleCredit>
      </div>
    </div>
  );
};

const TitleCredit = ({label, children}) => (
  <div
    style={{
      border: `1px solid ${C.line}`,
      borderRadius: 8,
      background: 'rgba(255,255,255,0.72)',
      boxShadow: '0 18px 44px rgba(40,42,62,0.08)',
      padding: '15px 18px 16px',
      minHeight: 94,
    }}
  >
    <div style={{fontSize: 19, color: C.blue, marginBottom: 8}}>{label}</div>
    <div style={{fontSize: 23, lineHeight: 1.05}}>{children}</div>
  </div>
);

const Header = ({act, frame, opacity = 1}) => {
  const y = interpolate(frame, [0, 28], [-18, 0], clamp);
  return (
    <div className="header" style={{opacity: fadeIn(frame, 0, 22) * opacity, transform: `translateY(${y}px)`}}>
      <div className="kicker">{act.kicker}</div>
      <h1 className="title">{act.title}</h1>
    </div>
  );
};

const LogoStrip = () => (
  <div
    style={{
      position: 'absolute',
      top: 24,
      right: 42,
      zIndex: 24,
      display: 'flex',
      alignItems: 'center',
      gap: 22,
      height: 60,
      pointerEvents: 'none',
      filter: 'drop-shadow(0 5px 10px rgba(40,42,62,0.12))',
    }}
  >
    <Img src={staticFile('hkust_logo_transparent.png')} style={{height: 50, width: 202, objectFit: 'contain'}} />
    <Img src={staticFile('ieda_logo_transparent.png')} style={{height: 50, width: 220, objectFit: 'contain'}} />
  </div>
);

const TransitionVeil = ({frame}) => {
  const opacity = ACTS.slice(1).reduce((best, act) => {
    const d = Math.abs(frame - act.start);
    if (d > 22) {
      return best;
    }
    return Math.max(best, 1 - d / 22);
  }, 0);
  return <div className="wipe" style={{opacity}} />;
};

const CaptionTrack = ({frame, beats}) => {
  const beat = beats.find((item) => frame >= item.start && frame < item.end);
  if (!beat) {
    return null;
  }
  return (
    <div className="narration" style={{opacity: segment(frame, beat.start, beat.end, 16)}}>
      {beat.text}
    </div>
  );
};

const MathTex = ({tex, display = false, className = '', style}) => {
  const html = useMemo(
    () =>
      katex.renderToString(tex, {
        displayMode: display,
        throwOnError: false,
        strict: 'ignore',
      }),
    [tex, display],
  );
  return <span className={`formula ${className}`} dangerouslySetInnerHTML={{__html: html}} style={style} />;
};

const Svg = ({children, style}) => (
  <svg height="720" style={{position: 'absolute', inset: 0, overflow: 'visible', ...style}} viewBox="0 0 1280 720" width="1280">
    {children}
  </svg>
);

const Panel = ({children, style}) => (
  <div className="panel" style={style}>
    {children}
  </div>
);

const Search = ({text, progress = 1, style}) => (
  <div className="search" style={style}>
    <div className="search-icon" />
    <div style={{width: `${progress * 100}%`, whiteSpace: 'nowrap', overflow: 'hidden'}}>{text}</div>
  </div>
);

const Chat = ({children, style, tone = C.blue}) => (
  <div className="chat" style={{borderColor: `${tone}40`, ...style}}>
    {children}
  </div>
);

const Packet = ({frame, from, to, color = C.blue, delay = 0, speed = 96, radius = 5}) => {
  const p = (((frame + delay) % speed) + speed) % speed / speed;
  const x = mix(from[0], to[0], p);
  const y = mix(from[1], to[1], p);
  return <circle cx={x} cy={y} fill={color} opacity={0.2 + 0.72 * Math.sin(Math.PI * p) ** 2} r={radius} />;
};

const FlowPath = ({frame, path, color = C.blue, delay = 0}) => {
  const p = ((frame + delay) % 120) / 120;
  const x = mix(path[0][0], path[1][0], p);
  const y = mix(path[0][1], path[1][1], p);
  return <circle cx={x} cy={y} fill={color} opacity={0.18 + 0.75 * Math.sin(Math.PI * p) ** 2} r="4.8" />;
};

const DotNode = ({x, y, label, color, frame, r = 30, opacity = 1}) => {
  const pulse = 1 + 0.04 * wave(frame, 0.055, x * 0.03);
  return (
    <g opacity={opacity} transform={`translate(${x} ${y}) scale(${pulse})`}>
      <circle fill={color} opacity="0.11" r={r + 15} stroke={color} strokeWidth="1.6" />
      <circle fill="#fff" r={r} stroke={color} strokeWidth="3" />
      {label ? (
        <text fill={C.ink} fontFamily="Instrument Serif" fontSize="20" textAnchor="middle" y="7">
          {label}
        </text>
      ) : null}
    </g>
  );
};

const Act1 = ({frame}) => {
  const zoom = interpolate(frame, [0, 190, 1092], [1.01, 1, 1.018], clamp);
  const x = interpolate(frame, [0, 1092], [0, -12], clamp);

  const beats = [
    {start: 0, end: 235, text: 'Imagine a cloud outage just happened in Virginia, which somehow grounds an airline and slows a London bank.'},
    {start: 235, end: 390, text: 'At first, it feels random. But one hidden phrase is quietly tying all three firms together.'},
    {start: 390, end: 515, text: 'A sector classifier says, "Different industries," and leaves the real dependency in its blind spot.'},
    {start: 515, end: 673, text: 'By the time prices fall together, the relationship is obvious, but the warning came too late.'},
    {start: 673, end: 854, text: 'We could search the open internet, but it quickly turns into posts, rumors, screenshots, and duplicates.'},
    {start: 854, end: 1092, text: 'So we turned to a more boring and more accountable document: the SEC 10-K, Item 1A, the part that keeps CEOs awake at night.'},
  ];

  return (
    <div className="scene">
      <div className="world" style={{transform: `translateX(${x}px) scale(${zoom})`}}>
        <UrgentNewsMorph frame={frame} opacity={segment(frame, 0, 270)} />
        <InfrastructureMap frame={frame - 232} opacity={segment(frame, 226, 390)} />
        <ClassifierPanel frame={frame} opacity={segment(frame, 392, 515)} />
        <CrashCharts frame={frame} opacity={segment(frame, 514, 673)} />
        <InternetNoise frame={frame} opacity={segment(frame, 664, 854)} />
        <RiskFilings frame={frame} opacity={segment(frame, 844, 1092)} />
      </div>
      <CaptionTrack beats={beats} frame={frame} />
    </div>
  );
};

const UrgentNewsMorph = ({frame, opacity}) => {
  const morph = et(frame, 172, 246);
  const highlightCloud = fadeIn(frame, 42, 18);
  const highlightFirms = fadeIn(frame, 68, 18);
  const highlightDependency = fadeIn(frame, 94, 18);
  const left = 232;
  const top = 160;
  const scale = mix(1, 0.17, morph);
  const radius = mix(8, 220, morph);
  const glow = 1 + 0.08 * wave(frame, 0.08);

  return (
    <div style={{opacity}}>
      <div
        className="panel"
        style={{
          left,
          top,
          width: 820,
          height: 282,
          padding: 24,
          overflow: 'hidden',
          borderRadius: radius,
          transform: `scale(${scale})`,
          transformOrigin: '48px 198px',
          opacity: 1 - t(frame, 232, 258),
          boxShadow: `0 24px ${70 + 24 * glow}px rgba(201,92,114,0.14)`,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
          <div style={{padding: '6px 12px', borderRadius: 999, background: C.rose, color: '#fff', fontSize: 21, lineHeight: 1}}>
            URGENT
          </div>
          <div className="label">Market infrastructure alert</div>
          <div style={{marginLeft: 'auto', color: C.muted, fontSize: 21}}>09:41 EST</div>
        </div>
        <div style={{marginTop: 25, fontSize: 48, lineHeight: 0.98}}>
          <span style={{background: `rgba(201,92,114,${0.18 * highlightCloud})`, color: highlightCloud ? C.rose : C.ink, borderRadius: 7}}>
            Cloud outage
          </span>{' '}
          in Virginia disrupts{' '}
          <span style={{background: `rgba(31,157,132,${0.16 * highlightFirms})`, color: highlightFirms ? C.teal : C.ink, borderRadius: 7}}>
            airline operations
          </span>{' '}
          as a London{' '}
          <span style={{background: `rgba(199,139,25,${0.16 * highlightFirms})`, color: highlightFirms ? C.amber : C.ink, borderRadius: 7}}>
            bank
          </span>{' '}
          reports trading delays.
        </div>
        <div style={{marginTop: 22, fontSize: 29, lineHeight: 1.08, color: C.muted}}>
          Common phrase found later:{' '}
          <span style={{color: C.blue, background: `rgba(83,103,240,${0.15 * highlightDependency})`, borderRadius: 6}}>
            reliance on third-party cloud infrastructure
          </span>
        </div>
      </div>
      <Svg style={{opacity: fadeIn(frame, 154, 22)}}>
        <circle cx="280" cy="358" fill="none" opacity={0.28 * morph} r={64 + 34 * morph} stroke={C.rose} strokeWidth="2.4" />
        <circle cx="280" cy="358" fill={C.rose} opacity={0.08 * morph} r={38 + 20 * morph} />
      </Svg>
    </div>
  );
};

const InfrastructureMap = ({frame, opacity = 1}) => {
  const outage = 1 + 0.12 * wave(frame, 0.07);
  const linkOpacity = fadeIn(frame, 24, 42);
  const server = [280, 358];
  const airline = [662, 250];
  const bank = [982, 286];
  return (
    <Svg style={{opacity}}>
      <g opacity={linkOpacity}>
        <path d="M210 520 C410 430 650 520 1080 430" fill="none" stroke="rgba(64,66,84,0.12)" strokeWidth="2" />
        <line stroke={C.blue} strokeDasharray="9 8" strokeLinecap="round" strokeWidth="3" x1={server[0]} x2={airline[0]} y1={server[1]} y2={airline[1]} />
        <line stroke={C.blue} strokeDasharray="9 8" strokeLinecap="round" strokeWidth="3" x1={server[0]} x2={bank[0]} y1={server[1]} y2={bank[1]} />
        <line stroke={C.amber} strokeDasharray="9 8" strokeLinecap="round" strokeWidth="2.4" x1={airline[0]} x2={bank[0]} y1={airline[1]} y2={bank[1]} />
        {[0, 34, 68].map((delay) => (
          <Packet color={C.blue} delay={delay} frame={frame} from={server} key={`a-${delay}`} to={airline} />
        ))}
        {[12, 48, 84].map((delay) => (
          <Packet color={C.amber} delay={delay} frame={frame} from={server} key={`b-${delay}`} to={bank} />
        ))}
      </g>
      {[0, 1, 2].map((i) => (
        <circle
          cx={server[0]}
          cy={server[1]}
          fill="none"
          key={i}
          opacity={(0.36 - i * 0.08) * segment(frame, 0, 190)}
          r={(62 + i * 34) * outage + ((frame + i * 20) % 60) * 0.55}
          stroke={C.rose}
          strokeWidth="2"
        />
      ))}
      <DotNode color={C.rose} frame={frame} label="Cloud" x={server[0]} y={server[1]} />
      <DotNode color={C.teal} frame={frame} label="Airline" opacity={fadeIn(frame, 38, 32)} x={airline[0]} y={airline[1]} />
      <DotNode color={C.amber} frame={frame} label="Bank" opacity={fadeIn(frame, 58, 32)} x={bank[0]} y={bank[1]} />
      <text fill={C.rose} fontFamily="Instrument Serif" fontSize="34" x="206" y="300">
        outage radius
      </text>
    </Svg>
  );
};

const ClassifierPanel = ({frame, opacity}) => {
  const eye = wave(frame, 0.09) * 7;
  const scan = 0.5 + 0.5 * wave(frame, 0.055);
  return (
    <div style={{opacity}}>
      <Panel style={{left: 770, top: 154, width: 420, height: 258, padding: 22}}>
        <div style={{fontSize: 31}}>Sector classifier</div>
        <div style={{display: 'grid', gap: 12, marginTop: 24, marginLeft: 8}}>
          <div className="chip" style={{color: C.teal}}>SIC 4512 Transportation</div>
          <div className="chip" style={{color: C.amber}}>SIC 6021 Financials</div>
          <div className="chip" style={{color: C.blue}}>SIC 7374 Cloud services</div>
        </div>
        <div
          style={{
            position: 'absolute',
            left: 34,
            top: 76,
            width: 336,
            height: 152,
            border: `2px dashed rgba(103,103,116,${0.55 + 0.14 * Math.sin(frame * 0.06) ** 2})`,
            borderRadius: 22,
            background: 'rgba(255,255,255,0.46)',
          }}
        />
      </Panel>
      <div style={{position: 'absolute', left: 850, top: 424, color: C.muted, fontSize: 19}}>
        blind spot covers all sector labels
      </div>
      <div
        style={{
          position: 'absolute',
          left: 588,
          top: 242,
          width: 118,
          height: 96,
          border: `2px solid ${C.line}`,
          borderRadius: 8,
          background: 'rgba(255,255,255,0.86)',
          boxShadow: '0 18px 48px rgba(40,42,62,0.08)',
        }}
      >
        <div style={{position: 'absolute', left: 32 + eye, top: 35, width: 9, height: 9, borderRadius: 99, background: C.blue}} />
        <div style={{position: 'absolute', left: 70 + eye, top: 35, width: 9, height: 9, borderRadius: 99, background: C.blue}} />
        <div style={{position: 'absolute', left: 26, right: 26, bottom: 22, height: 2, background: C.rose}} />
      </div>
      <svg height="260" style={{position: 'absolute', left: 584, top: 176, overflow: 'visible'}} viewBox="0 0 604 260" width="604">
        <path
          d="M104 116 C176 48 228 52 302 64"
          fill="none"
          opacity="0.42"
          stroke={C.teal}
          strokeDasharray="8 8"
          strokeLinecap="round"
          strokeWidth="2"
        />
        <path
          d="M104 116 C176 96 224 105 302 116"
          fill="none"
          opacity="0.45"
          stroke={C.amber}
          strokeDasharray="8 8"
          strokeLinecap="round"
          strokeWidth="2"
        />
        <path
          d="M104 116 C176 174 232 164 302 170"
          fill="none"
          opacity="0.38"
          stroke={C.blue}
          strokeDasharray="8 8"
          strokeLinecap="round"
          strokeWidth="2"
        />
        <line stroke={C.muted} strokeDasharray="5 8" strokeLinecap="round" strokeWidth="1.6" x1="300" x2="300" y1="48" y2="188" />
        <circle cx={132 + scan * 154} cy="116" fill={C.blue} opacity="0.58" r="3.5" />
      </svg>
    </div>
  );
};

const CrashCharts = ({frame, opacity}) => (
  <div style={{opacity}}>
    {[
      {left: 104, top: 160, label: 'CloudCo', ticker: 'CLD', price: '84.12'},
      {left: 420, top: 158, label: 'Airline', ticker: 'AIR', price: '31.47'},
      {left: 736, top: 158, label: 'Bank', ticker: 'BNK', price: '52.03'},
    ].map((chart, i) => (
      <MiniPriceChart frame={frame - 350 - i * 12} key={chart.label} {...chart} />
    ))}
  </div>
);

const MiniPriceChart = ({frame, left, top, label, ticker, price}) => {
  const p = et(frame, 0, 90);
  const pts = [
    [20, 72],
    [42, 68],
    [65, 71],
    [88, 66],
    [112, 75],
    [135, 70],
    [158, 84],
    [181, 82],
    [204, 124],
    [228, 136],
    [252, 147],
    [274, 158],
  ];
  const visible = Math.max(2, Math.floor(pts.length * p));
  const linePts = pts.slice(0, visible);
  const id = `drop-${ticker}`;
  const last = linePts[linePts.length - 1];
  const candles = [
    [24, 63, 78, 59, 84],
    [47, 70, 65, 61, 76],
    [70, 66, 73, 63, 78],
    [93, 72, 64, 59, 76],
    [116, 67, 78, 64, 84],
    [139, 76, 70, 66, 81],
    [162, 72, 87, 70, 93],
    [185, 84, 86, 78, 92],
    [208, 92, 124, 88, 131],
    [231, 122, 137, 118, 143],
    [254, 136, 148, 132, 154],
    [277, 147, 159, 143, 164],
  ];
  const volumes = [28, 34, 30, 38, 42, 36, 52, 58, 96, 86, 74, 88];
  return (
    <Panel style={{left, top, width: 286, height: 236, padding: 12}}>
      <div style={{display: 'flex', alignItems: 'baseline', justifyContent: 'space-between'}}>
        <div>
          <div style={{fontSize: 26, lineHeight: 0.95}}>{label}</div>
          <div className="label" style={{fontSize: 15, marginTop: 4}}>{ticker} / 1m candles</div>
        </div>
        <div style={{textAlign: 'right'}}>
          <div style={{fontSize: 21, color: C.rose}}>{price}</div>
          <div style={{fontSize: 16, color: C.rose}}>-7.8%</div>
        </div>
      </div>
      <svg height="168" viewBox="0 0 286 176" width="262" style={{marginTop: 5}}>
        <defs>
          <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={C.rose} stopOpacity="0.18" />
            <stop offset="100%" stopColor={C.rose} stopOpacity="0" />
          </linearGradient>
        </defs>
        <rect fill="rgba(255,255,255,0.45)" height="170" rx="6" stroke="rgba(64,66,84,0.08)" width="282" x="2" y="3" />
        {[0, 1, 2, 3].map((i) => <line className="grid-line" key={`h-${i}`} x1="18" x2="272" y1={34 + i * 32} y2={34 + i * 32} />)}
        {[0, 1, 2, 3, 4].map((i) => <line className="grid-line" key={`v-${i}`} x1={28 + i * 56} x2={28 + i * 56} y1="18" y2="150" />)}
        {volumes.slice(0, visible).map((volume, i) => (
          <rect
            fill={i > 7 ? C.rose : i % 2 ? C.blue : C.teal}
            height={volume * 0.34}
            key={i}
            opacity={i > 7 ? 0.36 : 0.22}
            rx="2"
            width="9"
            x={21 + i * 23}
            y={160 - volume * 0.34}
          />
        ))}
        {candles.slice(0, visible).map(([x, open, close, high, low], i) => {
          const down = close > open;
          const y = Math.min(open, close);
          const h = Math.max(4, Math.abs(close - open));
          return (
            <g key={i} opacity={0.82}>
              <line stroke={down ? C.rose : C.teal} strokeLinecap="round" strokeWidth="1.8" x1={x} x2={x} y1={high} y2={low} />
              <rect fill={down ? C.rose : C.teal} height={h} opacity={down ? 0.78 : 0.55} rx="2" width="10" x={x - 5} y={y} />
            </g>
          );
        })}
        {linePts.length > 2 ? (
          <path d={`M${toPoints(linePts)} L ${last[0]} 164 L 20 164 Z`} fill={`url(#${id})`} opacity="0.8" />
        ) : null}
        <polyline fill="none" points={toPoints(linePts)} stroke={C.rose} strokeLinecap="round" strokeLinejoin="round" strokeWidth="3.6" />
        <line stroke={C.amber} strokeDasharray="5 5" strokeLinecap="round" strokeWidth="1.6" x1="196" x2="196" y1="20" y2="156" />
        <text fill={C.amber} fontFamily="Instrument Serif" fontSize="13" x="203" y="34">outage</text>
        <line opacity={0.42} stroke={C.muted} strokeDasharray="4 5" x1={mix(36, 270, p)} x2={mix(36, 270, p)} y1="20" y2="162" />
        <circle cx={last[0]} cy={last[1]} fill={C.rose} r="4.5" />
        <text fill={C.muted} fontFamily="Instrument Serif" fontSize="12" x="238" y="34">VWAP</text>
        <text fill={C.rose} fontFamily="Instrument Serif" fontSize="12" x="238" y="58">SELL</text>
      </svg>
      <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 15, color: C.muted, marginTop: -4}}>
        <span>Vol spike</span>
        <span style={{color: C.rose}}>gap down</span>
      </div>
    </Panel>
  );
};

const InternetNoise = ({frame, opacity}) => {
  const words = [
    ['tweets', 134, 280, C.blue, 35],
    ['rumors', 458, 300, C.rose, 33],
    ['screenshots', 846, 274, C.violet, 31],
    ['duplicate news', 244, 398, C.amber, 32],
    ['forum panic', 648, 414, C.teal, 35],
    ['unverified', 918, 500, C.rose, 33],
    ['bot traffic', 512, 548, C.muted, 32],
  ];
  const logos = [
    {name: 'X', src: 'x_logo.jpg', left: 164, top: 210, size: 48},
    {name: 'Reddit', src: 'reddit_logo.png', left: 292, top: 224, size: 50},
    {name: 'Instagram', src: 'instagram_logo.svg', left: 426, top: 206, size: 50},
    {name: 'YouTube', src: 'youtube_logo.webp', left: 574, top: 226, size: 52},
  ];
  return (
    <div style={{opacity}}>
      <Search progress={t(frame, 542, 610)} style={{left: 330, top: 166, width: 720}} text="search the internet for hidden contagion edges" />
      {logos.map((logo, i) => (
        <div
          key={logo.name}
          style={{
            position: 'absolute',
            left: logo.left + 7 * wave(frame, 0.03, i),
            top: logo.top + 7 * wave(frame, 0.035, i + 2),
            width: logo.size + 18,
            height: logo.size + 18,
            borderRadius: 16,
            background: 'rgba(255,255,255,0.86)',
            border: `1px solid ${C.line}`,
            display: 'grid',
            placeItems: 'center',
            opacity: 0.56 + 0.28 * Math.sin(frame * 0.035 + i) ** 2,
            boxShadow: '0 12px 34px rgba(40,42,62,0.06)',
            transform: `rotate(${wave(frame, 0.018, i + 1) * 3}deg)`,
          }}
        >
          <Img
            alt={logo.name}
            src={staticFile(logo.src)}
            style={{
              width: logo.size,
              height: logo.size,
              objectFit: 'contain',
              borderRadius: logo.name === 'X' ? 10 : 8,
            }}
          />
        </div>
      ))}
      {words.map(([word, left, top, color, size], i) => (
        <div
          key={word}
          style={{
            position: 'absolute',
            left: left + 14 * wave(frame, 0.035 + i * 0.002, i),
            top: top + 10 * wave(frame, 0.04 + i * 0.002, i * 2),
            color,
            fontSize: size,
            opacity: 0.38 + 0.28 * Math.sin(frame * 0.04 + i) ** 2,
            transform: `rotate(${wave(frame, 0.025, i) * 6}deg)`,
          }}
        >
          {word}
        </div>
      ))}
      <Chat style={{left: 96, top: 528, width: 376}} tone={C.rose}>
        Too many claims. Too little structure.
      </Chat>
    </div>
  );
};

const RiskFilings = ({frame, opacity}) => {
  const glow = 0.5 + 0.5 * Math.sin(frame * 0.08) ** 2;
  return (
    <div style={{opacity}}>
      <FilingDoc label="Airline 10-K" left={196} top={142} glow={glow} />
      <FilingDoc label="Bank 10-K" left={706} top={142} glow={glow} />
      <Svg>
        <line stroke={C.amber} strokeDasharray="10 8" strokeLinecap="round" strokeWidth="3" x1="520" x2="706" y1="380" y2="380" />
        <Packet color={C.amber} frame={frame} from={[520, 380]} speed={84} to={[706, 380]} />
      </Svg>
    </div>
  );
};

const FilingDoc = ({left, top, label, glow}) => (
  <Panel style={{left, top, width: 376, height: 406, padding: 22}}>
    <div style={{fontSize: 30}}>{label}</div>
    <div className="label" style={{marginTop: 7}}>SEC Form 10-K, Item 1A</div>
    <div style={{display: 'grid', gap: 12, marginTop: 25}}>
      {[0.88, 0.74, 0.86, 0.62, 0.8].map((w, i) => (
        <div className="doc-line" key={i} style={{width: `${w * 100}%`}} />
      ))}
    </div>
    <div
      className="highlight"
      style={{
        marginTop: 30,
        padding: 13,
        fontSize: 27,
        lineHeight: 1.04,
        boxShadow: `0 0 ${18 * glow}px rgba(199,139,25,${0.24 * glow})`,
      }}
    >
      Reliance on third-party cloud infrastructure
    </div>
  </Panel>
);

const Act2 = ({frame}) => {
  const beats = [
    {start: 0, end: 166, text: 'The old approach was almost mechanical: count scary words and call the paragraph risky.'},
    {start: 166, end: 382, text: 'Here, we ask an encoder to read the whole sentence, not just the negative vocabulary.'},
    {start: 382, end: 562, text: 'It turns one messy paragraph into a coordinate: a 384-number fingerprint of meaning.'},
    {start: 562, end: 732, text: 'Now two paragraphs can sit close together, even when they do not use the same words.'},
  ];
  const cameraScale = interpolate(frame, [0, 472, 732], [1.0, 1.018, 1.0], clamp);
  const cameraX = interpolate(frame, [0, 472, 732], [0, -18, -8], clamp);
  return (
    <div className="scene">
      <div className="world" style={{transform: `translateX(${cameraX}px) scale(${cameraScale})`}}>
        <DictionaryCounter frame={frame} opacity={segment(frame, 0, 186)} />
        <EmbeddingMachine frame={frame} opacity={segment(frame, 176, 732)} />
      </div>
      <CaptionTrack beats={beats} frame={frame} />
    </div>
  );
};

const DictionaryCounter = ({frame, opacity}) => (
  <div style={{opacity}}>
    <Panel style={{left: 92, top: 166, width: 420, height: 324, padding: 26}}>
      <div style={{fontSize: 34}}>Dictionary sentiment</div>
      <div style={{display: 'grid', gap: 15, marginTop: 28}}>
        {['severe outages', 'adverse disruption', 'losses may impair', 'failure may harm'].map((line, i) => (
          <div key={line} style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <div style={{width: 12, height: 12, borderRadius: 99, background: C.rose}} />
            <div style={{fontSize: 28}}>{line}</div>
            <div style={{marginLeft: 'auto', color: C.rose, fontSize: 24}}>+1</div>
          </div>
        ))}
      </div>
    </Panel>
    <Abacus frame={frame} />
    <div
      style={{
        position: 'absolute',
        left: 242,
        top: 526,
        width: 654,
        minHeight: 74,
        padding: '12px 18px',
        border: `2px dashed rgba(201,92,114,${0.58 + 0.16 * Math.sin(frame * 0.05) ** 2})`,
        borderRadius: 8,
        background: 'rgba(255,255,255,0.88)',
        color: C.rose,
        fontSize: 25,
        lineHeight: 1.08,
        opacity: fadeIn(frame, 88, 20),
      }}
    >
      Inefficient: counts miss context, paraphrases, and shared dependencies hiding behind different words.
    </div>
  </div>
);

const Abacus = ({frame}) => (
  <Panel style={{left: 590, top: 176, width: 332, height: 304, padding: 26}}>
    <div style={{fontSize: 32}}>tally machine</div>
    <svg height="210" viewBox="0 0 300 200" width="280">
      {[0, 1, 2, 3].map((row) => (
        <g key={row}>
          <line stroke="rgba(64,66,84,0.26)" strokeWidth="2" x1="20" x2="280" y1={42 + row * 38} y2={42 + row * 38} />
          {[0, 1, 2, 3, 4].map((b) => {
            const shift = b <= row ? 22 * et(frame, 34 + row * 14, 100 + row * 14) : 0;
            return <circle cx={58 + b * 42 + shift} cy={42 + row * 38} fill={b <= row ? C.rose : '#fff'} key={b} r="12" stroke={b <= row ? C.rose : C.line} strokeWidth="2" />;
          })}
        </g>
      ))}
    </svg>
  </Panel>
);

const EmbeddingMachine = ({frame, opacity}) => {
  const flow = et(frame, 186, 382);
  const vectorP = et(frame, 382, 562);
  return (
    <div style={{opacity}}>
      <Panel style={{left: 122, top: 184, width: 350, height: 300, padding: 23}}>
        <div style={{fontSize: 31}}>Item 1A paragraph</div>
        <div className="highlight" style={{marginTop: 22, padding: 13, fontSize: 27, lineHeight: 1.05}}>
          Reliance on third-party cloud infrastructure may materially disrupt operations.
        </div>
      </Panel>
      <Panel style={{left: 532, top: 196, width: 232, height: 232, padding: 20, textAlign: 'center'}}>
        <div className="label">encoder</div>
        <div style={{height: 122, width: 122, borderRadius: 999, margin: '26px auto 0', border: `3px solid ${C.blue}`, boxShadow: `0 0 ${18 + 10 * wave(frame, 0.06) ** 2}px rgba(83,103,240,0.22)`, display: 'grid', placeItems: 'center'}}>
          <MathTex className="formula-blue" tex="f_\phi" style={{fontSize: 43}} />
        </div>
      </Panel>
      <TokenStream frame={frame} progress={flow} />
      <div style={{position: 'absolute', left: 806, top: 138, width: 408, height: 96, opacity: fadeIn(frame, 220, 22), textAlign: 'center'}}>
        <EquationBuild frame={frame} />
      </div>
      <VectorTunnel frame={frame} opacity={vectorP} />
      <Search progress={t(frame, 276, 382)} style={{left: 302, top: 526, width: 650}} text="embed paragraph into 384 semantic dimensions" />
    </div>
  );
};

const TokenStream = ({frame, progress}) => {
  const tokens = [
    {color: C.blue, y: 296},
    {color: C.teal, y: 322},
    {color: C.amber, y: 348},
    {color: C.violet, y: 374},
  ];
  return (
    <Svg>
      <path d="M420 334 C468 250 536 250 612 316" fill="none" opacity="0.18" stroke={C.blue} strokeDasharray="6 8" strokeWidth="2" />
      {tokens.map((token, i) => {
        const p = Math.max(0, Math.min(1, progress - i * 0.06));
        const x = mix(422, 612, p);
        const y = mix(token.y, 318, p) + Math.sin(p * Math.PI) * -48;
        const vanish = interpolate(p, [0.72, 1], [1, 0], clamp);
        return (
          <g key={token.color} opacity={fadeIn(frame, 170 + i * 12, 12) * vanish}>
            <circle cx={x} cy={y} fill={token.color} opacity="0.16" r="17" />
            <circle cx={x} cy={y} fill={token.color} r="6.5" />
            <circle cx={x - 17 * (1 - p)} cy={y + 7 * Math.sin(frame * 0.05 + i)} fill={token.color} opacity="0.25" r="3.5" />
          </g>
        );
      })}
    </Svg>
  );
};

const EquationBuild = ({frame}) => {
  const pieces = [
    {tex: '\\mathbf e_p', color: 'formula-blue'},
    {tex: '=', color: ''},
    {tex: 'f_\\phi(c_p)', color: 'formula-amber'},
    {tex: '\\in', color: ''},
    {tex: '\\mathbb R^{384}', color: 'formula-blue'},
  ];
  return (
    <div style={{display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: 15}}>
      {pieces.map((piece, i) => {
        const p = et(frame, 224 + i * 24, 274 + i * 24);
        return (
          <MathTex
            className={piece.color}
            key={piece.tex}
            tex={piece.tex}
            style={{fontSize: 42, opacity: p, transform: `translateY(${(1 - p) * 18}px)`, display: 'inline-block'}}
          />
        );
      })}
    </div>
  );
};

const VectorTunnel = ({frame, opacity}) => {
  const values = ['0.18', '-0.42', '0.07', '0.31', '-0.09', '...'];
  return (
    <div style={{opacity}}>
      <Panel style={{left: 812, top: 196, width: 408, height: 188, padding: 22}}>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8}}>
          <MathTex tex="[" style={{fontSize: 46}} />
          {values.map((value, i) => (
            <div
              key={value}
              style={{
                minWidth: 51,
                height: 46,
                display: 'grid',
                placeItems: 'center',
                border: `1px solid ${C.line}`,
                borderRadius: 7,
                color: i === values.length - 1 ? C.amber : C.blue,
                fontSize: 23,
                background: '#fff',
                transform: `translateY(${wave(frame, 0.05, i) * 3}px)`,
              }}
            >
              {value}
            </div>
          ))}
          <MathTex tex="]" style={{fontSize: 46}} />
        </div>
        <div className="label" style={{textAlign: 'center', marginTop: 22}}>384 coordinates</div>
      </Panel>
      <Svg>
        {Array.from({length: 24}).map((_, i) => {
          const p = i / 23;
          const x = 840 + p * 330;
          const h = 28 + 54 * Math.sin(frame * 0.032 + i) ** 2;
          return <rect fill={i % 5 === 0 ? C.amber : C.blue} height={h} key={i} opacity={0.12 + p * 0.32} rx="4" width={8 + p * 6} x={x} y={456 - h} />;
        })}
      </Svg>
    </div>
  );
};

const Act3 = ({frame}) => {
  const beats = [
    {start: 0, end: 250, text: 'Of course, nobody can picture 384 dimensions, so we project the neighborhood down to a 2-D map.'},
    {start: 250, end: 470, text: 'UMAP keeps nearby meanings near each other, and HDBSCAN lets dense areas become risk topics.'},
    {start: 470, end: 650, text: 'Then 2020 arrives, and companies begin describing a risk they did not talk about before.'},
    {start: 650, end: 888, text: 'The threshold theta is the gatekeeper. If a point drifts too far from old topics, the taxonomy makes room for a new one.'},
  ];
  return (
    <div className="scene">
      <SemanticPlane frame={frame} />
      <ProjectionHud frame={frame} />
      <CaptionTrack beats={beats} frame={frame} />
    </div>
  );
};

const semanticClusters = [
  {name: 'Supply chain', color: C.blue, c3: [-1.8, -0.2, -0.8], c2: [320, 322]},
  {name: 'Liquidity', color: C.teal, c3: [0.2, -0.15, 0.1], c2: [560, 378]},
  {name: 'Cloud reliance', color: C.amber, c3: [1.6, -0.05, -0.45], c2: [720, 238]},
  {name: 'Regulatory', color: C.violet, c3: [-0.55, 0.08, 1.25], c2: [424, 490]},
  {name: 'Pandemic disruption', color: C.rose, c3: [2.65, 0.02, 1.2], c2: [906, 468], late: true},
];

const semanticPoints = semanticClusters.flatMap((cluster, ci) =>
  Array.from({length: ci === 4 ? 22 : 28}).map((_, i) => {
    const seed = ci * 100 + i + 1;
    const a = rand(seed) * Math.PI * 2;
    const r = 0.12 + rand(seed + 2) * 0.42;
    return {
      ci,
      color: cluster.color,
      late: cluster.late,
      p3: [
        cluster.c3[0] + Math.cos(a) * r,
        cluster.c3[1] + (rand(seed + 8) - 0.5) * 0.34,
        cluster.c3[2] + Math.sin(a) * r,
      ],
      p2: [
        cluster.c2[0] + Math.cos(a) * (22 + rand(seed + 4) * 50),
        cluster.c2[1] + Math.sin(a) * (18 + rand(seed + 5) * 48),
      ],
    };
  }),
);

const project3D = ([x, y, z], rotY, rotX, scale = 145, cx = 640, cy = 395) => {
  const cosY = Math.cos(rotY);
  const sinY = Math.sin(rotY);
  const x1 = x * cosY + z * sinY;
  const z1 = -x * sinY + z * cosY;
  const cosX = Math.cos(rotX);
  const sinX = Math.sin(rotX);
  const y1 = y * cosX - z1 * sinX;
  const z2 = y * sinX + z1 * cosX;
  const perspective = 760 / (760 + z2 * 120);
  return {x: cx + x1 * scale * perspective, y: cy + y1 * scale * perspective, depth: z2, perspective};
};

const SemanticPlane = ({frame}) => {
  const newP = et(frame, 470, 610);
  const thetaP = fadeIn(frame, 620, 40);
  const rotation = interpolate(frame, [0, 420, 888], [-7, 5, -3], clamp);
  const skew = interpolate(frame, [0, 480, 888], [-9, 7, -5], clamp);
  const planeScale = 1 + 0.018 * Math.sin(frame * 0.018);
  const planeTransform = `translate(640 390) rotate(${rotation}) skewX(${skew}) scale(${planeScale} 0.92) translate(-640 -390)`;
  const radius = 92 + 8 * Math.sin(frame * 0.07);
  const sorted = [...semanticPoints].sort((a, b) => a.p2[1] - b.p2[1]);

  return (
    <Svg>
      <g transform={planeTransform}>
        <PlaneGrid />
        {sorted.map((point, i) => {
          const reveal = point.late ? newP : fadeIn(frame, 44 + i * 0.8, 30);
          return (
            <circle
              cx={point.p2[0]}
              cy={point.p2[1]}
              fill={point.color}
              key={`${point.ci}-${i}`}
              opacity={0.25 * reveal}
              r="13"
            />
          );
        })}
        {sorted.map((point, i) => {
          const reveal = point.late ? newP : fadeIn(frame, 44 + i * 0.8, 30);
          return (
            <circle
              cx={point.p2[0]}
              cy={point.p2[1]}
              fill={point.color}
              key={`core-${point.ci}-${i}`}
              opacity={0.72 * reveal}
              r="5"
            />
          );
        })}
        <g opacity={thetaP}>
          <ellipse
            cx="906"
            cy="468"
            fill="rgba(201,92,114,0.08)"
            rx={radius}
            ry={radius * 0.62}
            stroke={C.rose}
            strokeDasharray="10 8"
            strokeLinecap="round"
            strokeWidth="3"
          />
          <circle cx="906" cy="468" fill={C.amber} r="8" />
          <text fill={C.rose} fontFamily="Instrument Serif" fontSize="26" x="786" y="350">Pandemic disruption</text>
          <text fill={C.amber} fontFamily="Instrument Serif" fontSize="24" x="922" y="454">centroid</text>
        </g>
        <g opacity={fadeIn(frame, 320, 40)}>
          {semanticClusters.slice(0, 4).map((cluster) => (
            <text fill={cluster.color} fontFamily="Instrument Serif" fontSize="24" key={cluster.name} x={cluster.c2[0] - 64} y={cluster.c2[1] - 70}>
              {cluster.name}
            </text>
          ))}
        </g>
      </g>
    </Svg>
  );
};

const PlaneGrid = () => {
  const xs = Array.from({length: 9}, (_, i) => 240 + i * 92);
  const ys = Array.from({length: 6}, (_, i) => 210 + i * 72);
  return (
    <g opacity="0.76">
      <polygon fill="rgba(83,103,240,0.035)" points="208,178 1034,158 1086,568 260,596" stroke={C.line} strokeWidth="1.4" />
      {xs.map((x) => (
        <line className="grid-line" key={`x-${x}`} x1={x} x2={x + 54} y1="180" y2="592" />
      ))}
      {ys.map((y) => (
        <line className="grid-line" key={`y-${y}`} x1="210" x2="1082" y1={y} y2={y - 24} />
      ))}
      <text fill={C.muted} fontFamily="Instrument Serif" fontSize="24" x="184" y="592">2-D projection of semantic neighborhoods</text>
    </g>
  );
};

const ProjectionHud = ({frame}) => (
  <div>
    <Panel style={{left: 70, top: 150, width: 320, height: 168, padding: 20, opacity: segment(frame, 40, 410)}}>
      <div className="label">projection pipeline</div>
      <div style={{display: 'flex', gap: 10, marginTop: 18}}>
        <span className="chip" style={{color: C.blue}}>UMAP</span>
        <span className="chip" style={{color: C.teal}}>HDBSCAN</span>
      </div>
      <div style={{marginTop: 20, fontSize: 28}}>
        <MathTex tex="384D \rightarrow 2D" />
      </div>
    </Panel>
    <Panel style={{left: 70, top: 154, width: 344, height: 156, padding: 22, opacity: segment(frame, 620, 888)}}>
      <div className="label">semantic-deviation threshold</div>
      <div style={{marginTop: 18, display: 'flex', alignItems: 'center', gap: 18}}>
        <MathTex className="formula-amber" tex="\theta=0.40" style={{fontSize: 42}} />
        <div style={{height: 4, width: 118, background: C.line, borderRadius: 99}}>
          <div style={{height: 4, width: `${42 + 10 * wave(frame, 0.05) ** 2}%`, background: C.amber, borderRadius: 99}} />
        </div>
      </div>
    </Panel>
  </div>
);

const Act4 = ({frame}) => {
  const beats = [
    {start: 0, end: 222, text: 'Once every firm has a risk profile, the text stops being just a filing and starts becoming a network.'},
    {start: 222, end: 428, text: 'If two firms disclose similar risk vectors, we draw an edge, even when their sectors look unrelated.'},
    {start: 428, end: 668, text: 'ST-GAT means Spatio-Temporal Graph Attention Network: it reads the graph, the time history, and the strongest links together.'},
    {start: 688, end: 900, text: 'Attention weights decide which edges matter most, so volatility flows through the dependencies that actually carry information.'},
  ];
  return (
    <div className="scene">
      <TemporalGraph frame={frame} />
      <GraphHud frame={frame} />
      <CaptionTrack beats={beats} frame={frame} />
    </div>
  );
};

const graphBaseNodes = [
  {id: 'CloudCo', x: -2.15, y: -0.65, color: C.blue},
  {id: 'Airline', x: -0.98, y: 0.15, color: C.teal},
  {id: 'Bank', x: 0.32, y: -0.2, color: C.amber},
  {id: 'Retail', x: 1.55, y: 0.28, color: C.violet},
  {id: 'Logistics', x: -0.52, y: -1.08, color: C.rose},
  {id: 'Insurer', x: 1.05, y: -1.0, color: C.teal},
];

const graphEdges = [
  [0, 1, 3],
  [0, 4, 2],
  [1, 2, 5],
  [1, 4, 3],
  [2, 3, 4],
  [2, 5, 5],
  [4, 5, 3],
  [1, 5, 2],
];

const graphLabelRadius = (label) => Math.max(32, Math.min(46, 17 + label.length * 3.25));

const TemporalGraph = ({frame}) => {
  const rotY = interpolate(frame, [0, 900], [-0.58, 0.48], clamp);
  const rotX = interpolate(frame, [0, 900], [0.68, 0.8], clamp);
  const layers = [-1.55, 0, 1.55];
  const attention = et(frame, 688, 818);
  const graphP = fadeIn(frame, 44, 50);
  const layerP = et(frame, 428, 568);
  const graphScale = 116;
  const graphCx = 500;
  const graphCy = 430;

  const projected = layers.map((z, li) =>
    graphBaseNodes.map((node) => {
      const p = project3D([node.x, node.y, z], rotY, rotX, graphScale, graphCx, graphCy);
      return {...node, z, li, sx: p.x, sy: p.y, depth: p.depth, perspective: p.perspective};
    }),
  );

  return (
    <Svg>
      {layers.map((z, li) => {
        const corners = [
          project3D([-2.65, -1.42, z], rotY, rotX, graphScale, graphCx, graphCy),
          project3D([2.25, -1.42, z], rotY, rotX, graphScale, graphCx, graphCy),
          project3D([2.25, 0.82, z], rotY, rotX, graphScale, graphCx, graphCy),
          project3D([-2.65, 0.82, z], rotY, rotX, graphScale, graphCx, graphCy),
        ];
        const opacity = li === 2 ? 0.22 + 0.18 * layerP : 0.1 + li * 0.04;
        return (
          <g key={z} opacity={graphP * (li < 2 ? layerP : 1)}>
            <polygon fill={li === 2 ? 'rgba(83,103,240,0.06)' : 'rgba(255,255,255,0.28)'} points={corners.map((p) => `${p.x},${p.y}`).join(' ')} stroke={C.line} strokeWidth="1.4" opacity={opacity} />
            <text fill={C.muted} fontFamily="Instrument Serif" fontSize="22" x={corners[0].x + 8} y={corners[0].y - 10}>
              {li === 0 ? 't-2' : li === 1 ? 't-1' : 't'}
            </text>
          </g>
        );
      })}
      {projected.map((layer, li) => (
        <g key={li} opacity={graphP * (li < 2 ? layerP : 1)}>
          {graphEdges.map(([a, b, w], i) => {
            const from = layer[a];
            const to = layer[b];
            const hot = i === 2 || i === 5;
            const alpha = hot ? attention : 0;
            return (
              <g key={`${li}-${i}`}>
                <line stroke={hot ? C.amber : C.blue} strokeLinecap="round" strokeWidth={2 + w * 0.55 + alpha * 5} x1={from.sx} x2={to.sx} y1={from.sy} y2={to.sy} opacity={hot ? 0.28 + 0.5 * alpha : 0.18} />
                {li === 2 ? <Packet color={hot ? C.amber : C.blue} delay={i * 11} frame={frame} from={[from.sx, from.sy]} speed={100 - i * 3} to={[to.sx, to.sy]} /> : null}
              </g>
            );
          })}
        </g>
      ))}
      {graphBaseNodes.map((_, ni) => {
        const a = projected[0][ni];
        const b = projected[1][ni];
        const c = projected[2][ni];
        return (
          <g key={ni} opacity={layerP}>
            <line stroke={C.violet} strokeDasharray="5 7" strokeWidth="1.8" x1={a.sx} x2={b.sx} y1={a.sy} y2={b.sy} opacity="0.24" />
            <line stroke={C.violet} strokeDasharray="5 7" strokeWidth="1.8" x1={b.sx} x2={c.sx} y1={b.sy} y2={c.sy} opacity="0.24" />
          </g>
        );
      })}
      {[...projected.flat()].sort((a, b) => a.depth - b.depth).map((node, i) => (
        <g key={`${node.id}-${node.li}`} opacity={graphP * (node.li < 2 ? layerP * 0.65 : 1)} transform={`translate(${node.sx} ${node.sy}) scale(${0.78 + node.perspective * 0.13})`}>
          {(() => {
            const inner = node.li === 2 ? graphLabelRadius(node.id) : 28;
            const fontSize = node.id.length > 8 ? 16 : node.id.length > 6 ? 17 : 19;
            return (
              <>
                <circle fill={node.color} opacity="0.12" r={inner + 17} stroke={node.color} strokeWidth="1.5" />
                <circle fill="#fff" r={inner} stroke={node.color} strokeWidth="3" />
                {node.li === 2 ? (
                  <text fill={C.ink} fontFamily="Instrument Serif" fontSize={fontSize} textAnchor="middle" y="6">
                    {node.id}
                  </text>
                ) : null}
              </>
            );
          })()}
        </g>
      ))}
    </Svg>
  );
};

const GraphHud = ({frame}) => (
  <div>
    <Panel style={{left: 832, top: 166, width: 330, height: 132, padding: 20, opacity: segment(frame, 154, 430, 28)}}>
      <div className="label">Risk Edge rule</div>
      <div style={{marginTop: 18}}>
        <MathTex className="formula-blue" tex="\cos(\mathbf R_i,\mathbf R_j)>\tau" style={{fontSize: 32}} />
      </div>
    </Panel>
    <StGatAid frame={frame} opacity={segment(frame, 440, 678, 30)} />
    <Panel style={{left: 832, top: 430, width: 330, height: 132, padding: 22, opacity: segment(frame, 688, 900, 34)}}>
      <div className="label">attention on edge</div>
      <div style={{marginTop: 16, display: 'flex', alignItems: 'center', gap: 14}}>
        <MathTex className="formula-amber" tex="\alpha_{ij}" style={{fontSize: 50}} />
        <div style={{height: 46, width: 130, borderRadius: 999, background: 'rgba(199,139,25,0.13)', border: `1px solid ${C.amber}`, boxShadow: `0 0 ${20 + 12 * wave(frame, 0.06) ** 2}px rgba(199,139,25,0.22)`}} />
      </div>
    </Panel>
  </div>
);

const StGatAid = ({frame, opacity}) => {
  const glow = 0.45 + 0.35 * Math.sin(frame * 0.065) ** 2;
  return (
    <div style={{opacity}}>
      <Panel style={{left: 812, top: 158, width: 390, height: 216, padding: 18}}>
        <div className="label">ST-GAT</div>
        <div style={{fontSize: 28, lineHeight: 0.98, marginTop: 6}}>Spatio-Temporal Graph Attention Network</div>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginTop: 18}}>
          <AidCell title="spatial">
            <svg height="48" viewBox="0 0 96 48" width="96">
              <line stroke={C.blue} strokeLinecap="round" strokeWidth="3" x1="24" x2="72" y1="24" y2="24" />
              <circle cx="24" cy="24" fill="#fff" r="14" stroke={C.teal} strokeWidth="3" />
              <circle cx="72" cy="24" fill="#fff" r="14" stroke={C.amber} strokeWidth="3" />
              <circle cx={34 + 24 * (0.5 + 0.5 * wave(frame, 0.08))} cy="24" fill={C.blue} r="4.5" />
            </svg>
          </AidCell>
          <AidCell title="temporal">
            <svg height="48" viewBox="0 0 96 48" width="96">
              {[0, 1, 2].map((i) => (
                <g key={i} transform={`translate(${12 + i * 24} ${8 + i * 5})`}>
                  <rect fill="rgba(83,103,240,0.07)" height="25" rx="4" stroke={C.line} width="42" />
                  <text fill={C.muted} fontFamily="Instrument Serif" fontSize="12" x="10" y="17">{i === 0 ? 't-2' : i === 1 ? 't-1' : 't'}</text>
                </g>
              ))}
            </svg>
          </AidCell>
          <AidCell title="attention">
            <svg height="48" viewBox="0 0 96 48" width="96">
              <text fill={C.amber} fontFamily="Instrument Serif" fontSize="24" x="7" y="32">a_ij</text>
              <rect fill="rgba(199,139,25,0.1)" height="18" rx="9" stroke={C.amber} width="52" x="36" y="16" />
              <rect fill={C.amber} height="18" opacity={glow} rx="9" width={24 + 16 * glow} x="36" y="16" />
            </svg>
          </AidCell>
        </div>
      </Panel>
      <div
        className="label"
        style={{
          position: 'absolute',
          left: 812,
          top: 392,
          width: 390,
          padding: '10px 14px',
          borderRadius: 8,
          background: 'rgba(255,255,255,0.72)',
          border: `1px solid ${C.line}`,
          fontSize: 19,
          lineHeight: 1.08,
          boxShadow: '0 14px 42px rgba(40,42,62,0.07)',
        }}
      >
        Similar disclosures define edges; time layers carry the history; attention opens the strongest gates.
      </div>
    </div>
  );
};

const AidCell = ({title, children}) => (
  <div style={{border: `1px solid ${C.line}`, borderRadius: 8, background: 'rgba(255,255,255,0.6)', padding: '7px 5px 5px', textAlign: 'center'}}>
    <div style={{color: C.muted, fontSize: 16, lineHeight: 1}}>{title}</div>
    {children}
  </div>
);

const Act5 = ({frame}) => {
  const beats = [
    {start: 0, end: 222, text: 'After training, the network ranks firms by how exposed they are to these hidden transmission paths.'},
    {start: 222, end: 464, text: 'We buy the firms the model likes most, short the ones it likes least, and watch the spread open.'},
    {start: 464, end: 636, text: 'That is the takeaway: SEC boilerplate can become a living map of financial contagion.'},
  ];
  const creditWash = t(frame, 628, 676);
  return (
    <div className="scene">
      <PortfolioMechanism frame={frame} />
      <CaptionTrack beats={beats} frame={frame} />
      <AbsoluteFill style={{background: '#fbfbfd', opacity: creditWash, zIndex: 12}} />
      <EndCredits frame={frame} opacity={fadeIn(frame, 644, 36)} />
    </div>
  );
};

const rankNodes = [
  {id: 'C01', x: 256, y: 270, color: C.teal, score: '0.96'},
  {id: 'C07', x: 404, y: 202, color: C.teal, score: '0.91'},
  {id: 'C12', x: 554, y: 278, color: C.teal, score: '0.88'},
  {id: 'C18', x: 714, y: 214, color: C.teal, score: '0.83'},
  {id: 'C23', x: 338, y: 416, color: C.rose, score: '0.19'},
  {id: 'C31', x: 506, y: 436, color: C.rose, score: '0.12'},
  {id: 'C44', x: 674, y: 406, color: C.rose, score: '0.09'},
  {id: 'C52', x: 852, y: 350, color: C.rose, score: '0.05'},
];

const PortfolioMechanism = ({frame}) => {
  const split = et(frame, 56, 190);
  const rank = segment(frame, 0, 222, 30);
  const chart = segment(frame, 234, 464, 30);
  const web = segment(frame, 484, 732, 36);
  return (
    <div>
      <Svg style={{opacity: rank}}>
        <line stroke={C.line} strokeDasharray="8 8" x1="170" x2="1040" y1="334" y2="334" />
        {rankNodes.map((node, i) => {
          const target = i < 4 ? [250 + i * 170, 204] : [250 + (i - 4) * 170, 464];
          const x = mix(node.x, target[0], split);
          const y = mix(node.y, target[1], split);
          return (
            <g key={node.id}>
              <DotNode color={node.color} frame={frame} label={node.id} r={27} x={x} y={y} />
              <text fill={node.color} fontFamily="Instrument Serif" fontSize="20" textAnchor="middle" x={x} y={y + 62}>
                {node.score}
              </text>
            </g>
          );
        })}
        <text fill={C.teal} fontFamily="Instrument Serif" fontSize="30" opacity={split} x="890" y="202">highest signal</text>
        <text fill={C.rose} fontFamily="Instrument Serif" fontSize="30" opacity={split} x="890" y="464">lowest signal</text>
      </Svg>
      <Backtest frame={frame - 234} opacity={chart} />
      <FinalTopology frame={frame} opacity={web} />
    </div>
  );
};

const Backtest = ({frame, opacity}) => {
  const p = et(frame, 30, 150);
  const top = [
    [82, 278],
    [130, 262],
    [178, 246],
    [228, 225],
    [278, 216],
    [330, 188],
    [382, 176],
    [434, 152],
    [486, 130],
    [540, 112],
    [594, 98],
    [648, 84],
    [704, 73],
    [760, 62],
  ];
  const bottom = [
    [82, 278],
    [130, 286],
    [178, 293],
    [228, 306],
    [278, 318],
    [330, 322],
    [382, 334],
    [434, 348],
    [486, 358],
    [540, 368],
    [594, 376],
    [648, 387],
    [704, 397],
    [760, 404],
  ];
  const topPts = top.slice(0, Math.max(2, Math.floor(top.length * p)));
  const bottomPts = bottom.slice(0, Math.max(2, Math.floor(bottom.length * p)));
  const topLast = topPts[topPts.length - 1];
  const bottomLast = bottomPts[bottomPts.length - 1];
  const markerX = mix(82, 760, p);
  const volume = [42, 38, 46, 40, 54, 58, 64, 60, 72, 66, 76, 82, 78, 88];
  return (
    <div style={{opacity}}>
      <Panel style={{left: 92, top: 128, width: 1006, height: 480, padding: 0, overflow: 'hidden'}}>
        <div
          style={{
            height: 54,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 22px',
            borderBottom: `1px solid ${C.line}`,
            background: 'rgba(255,255,255,0.48)',
          }}
        >
          <div style={{fontSize: 26}}>Long-short portfolio backtest</div>
          <div style={{display: 'flex', gap: 18, fontSize: 18, color: C.muted}}>
            <span>monthly rebalance</span>
            <span style={{color: C.teal}}>top decile</span>
            <span style={{color: C.rose}}>bottom decile</span>
          </div>
        </div>
        <svg height="426" viewBox="0 0 1006 426" width="1006">
          <defs>
            <linearGradient id="top-portfolio-fill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={C.teal} stopOpacity="0.16" />
              <stop offset="100%" stopColor={C.teal} stopOpacity="0" />
            </linearGradient>
            <linearGradient id="bottom-portfolio-fill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={C.rose} stopOpacity="0" />
              <stop offset="100%" stopColor={C.rose} stopOpacity="0.15" />
            </linearGradient>
          </defs>
          <rect fill="rgba(255,255,255,0.38)" height="350" rx="8" stroke="rgba(64,66,84,0.08)" width="842" x="58" y="38" />
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <line className="grid-line" key={`h-${i}`} x1="70" x2="880" y1={62 + i * 57} y2={62 + i * 57} />
          ))}
          {[0, 1, 2, 3, 4, 5, 6].map((i) => (
            <line className="grid-line" key={`v-${i}`} x1={82 + i * 113} x2={82 + i * 113} y1="52" y2="404" />
          ))}
          <line className="axis" x1="70" x2="880" y1="278" y2="278" />
          <line className="axis" x1="70" x2="70" y1="52" y2="404" />
          {['+18%', '+12%', '+6%', '0%', '-6%', '-12%'].map((label, i) => (
            <text fill={C.muted} fontFamily="Instrument Serif" fontSize="15" key={label} textAnchor="end" x="57" y={68 + i * 57}>{label}</text>
          ))}
          {['2019', '2020', '2021', '2022', '2023', '2024'].map((label, i) => (
            <text fill={C.muted} fontFamily="Instrument Serif" fontSize="15" key={label} textAnchor="middle" x={82 + i * 136} y="417">{label}</text>
          ))}
          {volume.slice(0, Math.max(2, Math.floor(volume.length * p))).map((h, i) => (
            <rect
              fill={i % 3 === 0 ? C.amber : i % 2 ? C.blue : C.teal}
              height={h * 0.46}
              key={i}
              opacity="0.18"
              rx="2"
              width="24"
              x={72 + i * 52}
              y={404 - h * 0.46}
            />
          ))}
          {topPts.length > 2 ? <path d={`M${toPoints(topPts)} L ${topLast[0]} 278 L 82 278 Z`} fill="url(#top-portfolio-fill)" /> : null}
          {bottomPts.length > 2 ? <path d={`M${toPoints(bottomPts)} L ${bottomLast[0]} 278 L 82 278 Z`} fill="url(#bottom-portfolio-fill)" /> : null}
          <polyline fill="none" points={toPoints(topPts)} stroke={C.teal} strokeLinecap="round" strokeLinejoin="round" strokeWidth="4.8" />
          <polyline fill="none" points={toPoints(bottomPts)} stroke={C.rose} strokeLinecap="round" strokeLinejoin="round" strokeWidth="4.8" />
          <line opacity="0.32" stroke={C.muted} strokeDasharray="5 7" strokeLinecap="round" x1={markerX} x2={markerX} y1="52" y2="404" />
          <circle cx={topLast[0]} cy={topLast[1]} fill={C.teal} r="8" />
          <circle cx={bottomLast[0]} cy={bottomLast[1]} fill={C.rose} r="8" />
          <rect fill="rgba(255,255,255,0.86)" height="34" rx="7" stroke="rgba(31,157,132,0.28)" width="130" x="772" y="42" />
          <text fill={C.teal} fontFamily="Instrument Serif" fontSize="24" x="786" y="66">Top portfolio</text>
          <rect fill="rgba(255,255,255,0.88)" height="34" rx="7" stroke="rgba(201,92,114,0.28)" width="156" x="704" y="356" />
          <text fill={C.rose} fontFamily="Instrument Serif" fontSize="24" x="718" y="380">Bottom portfolio</text>
          <line stroke={C.amber} strokeLinecap="round" strokeWidth="4" x1="948" x2="948" y1="62" y2="404" />
          <path d="M928 62 H968 M928 404 H968" fill="none" stroke={C.amber} strokeLinecap="round" strokeWidth="4" />
          <text fill={C.amber} fontFamily="Instrument Serif" fontSize="46" x="604" y="238">16.26%</text>
          <text fill={C.ink} fontFamily="Instrument Serif" fontSize="34" x="604" y="276">annualized spread</text>
          <rect fill="rgba(199,139,25,0.1)" height="34" rx="17" stroke="rgba(199,139,25,0.25)" width="174" x="604" y="296" />
          <text fill={C.amber} fontFamily="Instrument Serif" fontSize="20" x="622" y="319">long top / short bottom</text>
        </svg>
      </Panel>
    </div>
  );
};

const FinalTopology = ({frame, opacity}) => {
  const nodes = [
    [240, 220, C.blue],
    [390, 150, C.teal],
    [560, 214, C.amber],
    [748, 154, C.violet],
    [902, 250, C.rose],
    [316, 442, C.rose],
    [514, 500, C.blue],
    [708, 438, C.teal],
    [898, 492, C.amber],
  ];
  const edges = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 4],
    [0, 5],
    [1, 6],
    [2, 6],
    [2, 7],
    [3, 7],
    [4, 8],
    [5, 6],
    [6, 7],
    [7, 8],
    [1, 7],
  ];
  return (
    <div style={{opacity}}>
      <Svg>
        {edges.map(([a, b], i) => {
          const from = [nodes[a][0], nodes[a][1] + 34];
          const to = [nodes[b][0], nodes[b][1] + 34];
          return (
            <g key={i}>
              <line stroke={i % 4 === 0 ? C.amber : C.blue} strokeLinecap="round" strokeWidth={2 + (i % 3)} x1={from[0]} x2={to[0]} y1={from[1]} y2={to[1]} opacity={0.24 + 0.22 * Math.sin(frame * 0.05 + i) ** 2} />
              <Packet color={[C.blue, C.teal, C.amber, C.rose][i % 4]} delay={i * 13} frame={frame} from={[from[0], from[1]]} speed={95} to={[to[0], to[1]]} />
            </g>
          );
        })}
        {nodes.map(([x, y, color], i) => <DotNode color={color} frame={frame} key={i} label="" r={23} x={x} y={y + 34} />)}
      </Svg>
    </div>
  );
};

const EndCredits = ({frame, opacity}) => {
  const y = interpolate(frame, [620, 672], [18, 0], clamp);
  return (
    <div
      style={{
        position: 'absolute',
        left: 128,
        right: 128,
        top: 82,
        zIndex: 18,
        opacity,
        transform: `translateY(${y}px)`,
        textAlign: 'center',
        color: C.ink,
        pointerEvents: 'none',
      }}
    >
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 20}}>
        <div style={{fontSize: 24, color: C.blue, marginBottom: 8}}>Live demo</div>
        <div
          style={{
            border: `1px solid ${C.line}`,
            borderRadius: 8,
            background: 'rgba(255,255,255,0.74)',
            color: C.ink,
            fontSize: 21,
            padding: '10px 16px',
          }}
        >
          web-2vkfru0n5-marco-choi-s-projects.vercel.app
        </div>
      </div>
      <div style={{fontSize: 24, color: C.blue, marginBottom: 10}}>Research team</div>
      <div style={{fontSize: 39, lineHeight: 1.05}}>
        CHAN Ho Lam Myles&nbsp;&nbsp;|&nbsp;&nbsp;CHOI Man Hou&nbsp;&nbsp;|&nbsp;&nbsp;TSOI Ching Yi
      </div>
      <div style={{fontSize: 27, color: C.muted, marginTop: 14}}>Dual Degree Program, HKUST</div>
      <div style={{fontSize: 23, color: C.blue, marginTop: 36}}>Supervisor</div>
      <div style={{fontSize: 34, marginTop: 8}}>Dr. Jiang Wei</div>
      <div style={{fontSize: 23, color: C.muted, marginTop: 8}}>IEDA Department, HKUST</div>
      <div style={{fontSize: 21, color: C.blue, marginTop: 22}}>Industry partner</div>
      <div style={{marginTop: 8, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 14}}>
        <Img
          src={staticFile('worldquant_logo.jpg')}
          style={{
            width: 70,
            height: 70,
            objectFit: 'contain',
            borderRadius: 8,
            boxShadow: '0 10px 30px rgba(40,42,62,0.08)',
          }}
        />
        <div style={{fontSize: 31}}>WorldQuant</div>
      </div>
    </div>
  );
};
