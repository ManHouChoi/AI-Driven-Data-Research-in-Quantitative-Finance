import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const C = {
  ink: '#171719',
  muted: '#676774',
  line: 'rgba(64,66,84,0.18)',
  blue: '#5367f0',
  teal: '#1f9d84',
  amber: '#c78b19',
  rose: '#c95c72',
  violet: '#7c6ff0',
};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const ease = Easing.bezier(0.22, 0.8, 0.24, 1);
const mix = (a, b, p) => a + (b - a) * p;
const wave = (frame, speed = 1, phase = 0) => Math.sin(frame * speed + phase);
const pointMix = (a, b, p) => ({x: mix(a.x, b.x, p), y: mix(a.y, b.y, p)});

const graphBaseNodes = [
  {id: 'CloudCo', x: -2.15, y: -0.65, color: C.blue},
  {id: 'Airline', x: -0.98, y: 0.15, color: C.teal},
  {id: 'Bank', x: 0.32, y: -0.2, color: C.amber},
  {id: 'Retail', x: 1.55, y: 0.28, color: C.violet},
  {id: 'Logistics', x: -0.52, y: -1.08, color: C.rose},
  {id: 'Insurer', x: 1.05, y: -1.0, color: C.teal},
  {id: '', x: -2.4, y: 0.58, color: C.blue},
  {id: '', x: -0.58, y: 0.86, color: C.teal},
  {id: '', x: 0.42, y: 0.86, color: C.amber},
  {id: '', x: 1.7, y: 0.86, color: C.violet},
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
  [6, 7, 2],
  [7, 8, 5],
  [8, 9, 3],
  [6, 1, 2],
  [7, 2, 3],
  [8, 3, 2],
];

const layerColors = [
  {label: 't', fill: 'rgba(83,103,240,0.13)', stroke: 'rgba(83,103,240,0.48)', text: C.blue},
  {label: 't+1', fill: 'rgba(31,157,132,0.12)', stroke: 'rgba(31,157,132,0.44)', text: C.teal},
  {label: 't+2', fill: 'rgba(199,139,25,0.13)', stroke: 'rgba(199,139,25,0.48)', text: C.amber},
];

const project3D = ([x, y, z], rotY, rotX, scale = 168, cx = 960, cy = 542) => {
  const cosY = Math.cos(rotY);
  const sinY = Math.sin(rotY);
  const x1 = x * cosY + z * sinY;
  const z1 = -x * sinY + z * cosY;
  const cosX = Math.cos(rotX);
  const sinX = Math.sin(rotX);
  const y1 = y * cosX - z1 * sinX;
  const z2 = y * sinX + z1 * cosX;
  const perspective = 940 / (940 + z2 * 125);
  return {
    x: cx + x1 * scale * perspective,
    y: cy + y1 * scale * perspective,
    depth: z2,
    perspective,
  };
};

const Packet = ({frame, from, to, color = C.blue, delay = 0, speed = 104, radius = 7}) => {
  const p = (((frame + delay) % speed) + speed) % speed / speed;
  const x = mix(from.x, to.x, p);
  const y = mix(from.y, to.y, p);
  return (
    <circle
      cx={x}
      cy={y}
      fill={color}
      opacity={0.18 + 0.76 * Math.sin(Math.PI * p) ** 2}
      r={radius}
    />
  );
};

const Node = ({frame, node}) => {
  const pulse = 1 + 0.05 * wave(frame, 0.055, node.x * 0.025 + node.y * 0.01);
  const radius = node.id ? Math.max(42, 21 + node.id.length * 4.1) : 34;
  const fontSize = node.id.length > 8 ? 22 : node.id.length > 6 ? 24 : 28;

  return (
    <g
      opacity={node.opacity}
      transform={`translate(${node.sx} ${node.sy}) scale(${pulse * (0.86 + node.perspective * 0.11)})`}
    >
      <circle fill={node.color} opacity="0.13" r={radius + 22} stroke={node.color} strokeWidth="1.8" />
      <circle fill="#fff" r={radius} stroke={node.color} strokeWidth="4.2" />
      {node.id ? (
        <text fill={C.ink} fontFamily="Instrument Serif" fontSize={fontSize} textAnchor="middle" y="8">
          {node.id}
        </text>
      ) : null}
    </g>
  );
};

const Plane = ({corners, frame, layer, opacity}) => {
  const color = layerColors[layer];
  const topLeft = corners[0];
  const topRight = corners[1];
  const bottomRight = corners[2];
  const bottomLeft = corners[3];
  const shimmer = 0.72 + 0.2 * Math.sin(frame * 0.035 + layer);

  return (
    <g opacity={opacity}>
      <polygon
        fill={color.fill}
        points={corners.map((p) => `${p.x},${p.y}`).join(' ')}
        stroke={color.stroke}
        strokeWidth="2.2"
      />
      {Array.from({length: 6}, (_, i) => (i + 1) / 7).map((p) => {
        const a = pointMix(topLeft, bottomLeft, p);
        const b = pointMix(topRight, bottomRight, p);
        return (
          <line
            key={`h-${p}`}
            opacity={0.34 * shimmer}
            stroke={color.stroke}
            strokeWidth="1.2"
            x1={a.x}
            x2={b.x}
            y1={a.y}
            y2={b.y}
          />
        );
      })}
      {Array.from({length: 8}, (_, i) => (i + 1) / 9).map((p) => {
        const a = pointMix(topLeft, topRight, p);
        const b = pointMix(bottomLeft, bottomRight, p);
        return (
          <line
            key={`v-${p}`}
            opacity={0.28 * shimmer}
            stroke={color.stroke}
            strokeWidth="1.1"
            x1={a.x}
            x2={b.x}
            y1={a.y}
            y2={b.y}
          />
        );
      })}
      <text
        fill={color.text}
        fontFamily="Instrument Serif"
        fontSize="42"
        fontWeight="400"
        opacity="0.9"
        x={topLeft.x + 18}
        y={topLeft.y - 16}
      >
        {color.label}
      </text>
    </g>
  );
};

export const STGATNetworkSpin = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = frame / Math.max(1, durationInFrames - 1);
  const entrance = ease(interpolate(frame, [0, 26], [0, 1], clamp));
  const exit = interpolate(frame, [durationInFrames - 24, durationInFrames - 1], [1, 0], clamp);
  const opacity = entrance * exit;

  const rotY = -0.62 + progress * Math.PI * 2;
  const rotX = 0.7 + 0.08 * Math.sin(progress * Math.PI * 2);
  const layers = [-1.58, 0, 1.58];

  const projected = layers.map((z, li) =>
    graphBaseNodes.map((node) => {
      const p = project3D([node.x, node.y, z], rotY, rotX);
      return {
        ...node,
        z,
        li,
        sx: p.x,
        sy: p.y,
        depth: p.depth,
        perspective: p.perspective,
        opacity: li === 2 ? 0.98 : 0.5 + li * 0.16,
      };
    }),
  );

  const planes = layers.map((z, li) => {
    const corners = [
      project3D([-2.86, -1.5, z], rotY, rotX),
      project3D([2.26, -1.5, z], rotY, rotX),
      project3D([2.26, 1.12, z], rotY, rotX),
      project3D([-2.86, 1.12, z], rotY, rotX),
    ];
    const depth = corners.reduce((sum, p) => sum + p.depth, 0) / corners.length;
    return {corners, depth, li};
  });

  return (
    <AbsoluteFill
      style={{
        background: '#ffffff',
        overflow: 'hidden',
      }}
    >
      <svg height="1080" style={{position: 'absolute', inset: 0, opacity}} viewBox="0 0 1920 1080" width="1920">
        <defs>
          <filter id="network-soft-shadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="28" floodColor="rgba(32,38,70,0.22)" stdDeviation="22" />
          </filter>
        </defs>
        <g filter="url(#network-soft-shadow)">
          {[...planes].sort((a, b) => a.depth - b.depth).map((plane) => (
            <Plane
              corners={plane.corners}
              frame={frame}
              key={plane.li}
              layer={plane.li}
              opacity={plane.li === 2 ? 0.94 : 0.68 + plane.li * 0.12}
            />
          ))}
          {projected.map((layer, li) => (
            <g key={`edges-${li}`} opacity={li === 2 ? 1 : 0.56 + li * 0.16}>
              {graphEdges.map(([a, b, w], i) => {
                const from = layer[a];
                const to = layer[b];
                const hot = i === 2 || i === 5 || i === 9;
                const glow = hot ? 0.42 + 0.42 * Math.sin(frame * 0.044 + i) ** 2 : 0;
                return (
                  <g key={`${li}-${i}`}>
                    <line
                      stroke={hot ? C.amber : C.blue}
                      strokeLinecap="round"
                      strokeWidth={2.6 + w * 0.62 + glow * 7}
                      x1={from.sx}
                      x2={to.sx}
                      y1={from.sy}
                      y2={to.sy}
                      opacity={hot ? 0.35 + glow : 0.2}
                    />
                    <Packet
                      color={hot ? C.amber : li === 1 ? C.teal : C.blue}
                      delay={i * 11 + li * 17}
                      frame={frame}
                      from={from}
                      radius={hot ? 7.5 : 5.6}
                      speed={116 - i * 2}
                      to={to}
                    />
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
              <g key={`temporal-${ni}`}>
                <line
                  stroke={C.violet}
                  strokeDasharray="9 10"
                  strokeLinecap="round"
                  strokeWidth="2.4"
                  x1={a.sx}
                  x2={b.sx}
                  y1={a.sy}
                  y2={b.sy}
                  opacity="0.32"
                />
                <line
                  stroke={C.violet}
                  strokeDasharray="9 10"
                  strokeLinecap="round"
                  strokeWidth="2.4"
                  x1={b.sx}
                  x2={c.sx}
                  y1={b.sy}
                  y2={c.sy}
                  opacity="0.36"
                />
              </g>
            );
          })}
          {[...projected.flat()]
            .sort((a, b) => a.depth - b.depth)
            .map((node) => (
              <Node frame={frame} key={`${node.id || 'empty'}-${node.li}-${node.x}`} node={node} />
            ))}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
