// Your House — live energy flow, simplified & readable.
function HouseTab() {
  const [tick, setTick] = React.useState(0);

  React.useEffect(() => {
    let raf;
    const start = performance.now();
    const loop = () => {
      setTick((performance.now() - start) / 1000);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  const scene = {
    solarKw: 3.8, useKw: 1.2, surplus: 2.6,
    caption: 'You are generating more than you use. The extra is powering 2 neighbours.',
  };

  return (
    <div className="pw-screen">
      <TabHeader eyebrow="Your house" title="Status"/>

      <div style={{ padding: '0 0 90px' }}>
        {/* Visualization canvas */}
        <div style={{
          margin: '0 16px',
          height: 360, position: 'relative',
          borderRadius: 'var(--r-lg)',
          background: 'linear-gradient(180deg, #F5EFE0 0%, #E8F2E4 100%)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <HouseScene tick={tick}/>
        </div>

        {/* Insight — dark card, matches Community/Dashboard style */}
        <div style={{ padding: '24px 24px 0' }}>
          <div style={{
            padding: '16px 18px',
            background: 'var(--ink-900)', color: '#fff',
            borderRadius: 'var(--r-md)',
            display: 'flex', alignItems: 'flex-start', gap: 12,
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'rgba(0,192,111,0.20)', color: 'var(--lime-400)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <IconBolt size={16}/>
            </div>
            <div style={{
              flex: 1,
              fontSize: 14, lineHeight: 1.45, fontWeight: 500,
              color: '#fff', letterSpacing: '-0.005em',
              textWrap: 'pretty',
            }}>
              {scene.caption}
            </div>
          </div>
        </div>

        {/* Live readouts */}
        <div style={{ padding: '20px 24px 0' }}>
          <div className="t-label" style={{ color: 'var(--ink-400)', marginBottom: 12 }}>
            Live readouts
          </div>
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10,
          }}>
            <Readout icon={<IconSolar size={14}/>} label="Generating" value={scene.solarKw.toFixed(1)} unit="kW" accent/>
            <Readout icon={<IconHome size={14}/>}  label="Using"      value={scene.useKw.toFixed(1)}  unit="kW"/>
            <Readout icon={<IconArrowRight size={14}/>} label="Surplus" value={scene.surplus.toFixed(1)} unit="kW" accent/>
          </div>
        </div>
      </div>
    </div>
  );
}

function Readout({ icon, label, value, unit, accent }) {
  return (
    <div style={{
      padding: '12px 12px',
      background: accent ? 'var(--lime-50)' : 'var(--surface)',
      border: '1px solid ' + (accent ? 'var(--lime-100)' : 'var(--cream-200)'),
      borderRadius: 'var(--r-md)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 5,
        color: accent ? 'var(--lime-600)' : 'var(--ink-400)', marginBottom: 6,
      }}>
        {icon}
        <span className="t-label" style={{ fontSize: 9 }}>{label}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
        <span className="t-num" style={{
          fontSize: 18, color: 'var(--ink-900)', fontWeight: 600,
          letterSpacing: '-0.03em',
        }}>{value}</span>
        <span style={{ fontSize: 10, color: 'var(--ink-400)', fontWeight: 500 }}>{unit}</span>
      </div>
    </div>
  );
}

// Layout: SUN top-center, HOUSE middle-center, GRID bottom-left, COMMUNITY bottom-right.
// Flows: sun → home, home → community ONLY.
function HouseScene({ tick }) {
  // Equal-spaced base nodes for grid + community
  const HOUSE_X = 180, HOUSE_Y = 175;
  const GRID_X = 90,  GRID_Y = 290;
  const COMM_X = 270, COMM_Y = 290;
  const SUN_X = 180,  SUN_Y = 55;

  return (
    <svg viewBox="0 0 360 360" style={{ width: '100%', height: '100%', display: 'block' }}>
      <defs>
        <radialGradient id="sunGlow" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%"  stopColor="#FFE8A0" stopOpacity="0.9"/>
          <stop offset="60%" stopColor="#FFD46A" stopOpacity="0.2"/>
          <stop offset="100%" stopColor="#FFD46A" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id="roofGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"  stopColor="#2A3A34"/>
          <stop offset="100%" stopColor="#1A2A24"/>
        </linearGradient>
        <linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"  stopColor="#1a3c2e"/>
          <stop offset="100%" stopColor="#0e2a1f"/>
        </linearGradient>
      </defs>

      {/* Ground hint */}
      <line x1="0" y1="320" x2="360" y2="320" stroke="rgba(0,168,98,0.15)" strokeWidth="1" strokeDasharray="2 4"/>

      {/* SUN */}
      <g>
        <circle cx={SUN_X} cy={SUN_Y} r="44" fill="url(#sunGlow)"/>
        <circle cx={SUN_X} cy={SUN_Y} r="20" fill="#FFC94A"/>
        {[0, 45, 90, 135, 180, 225, 270, 315].map(a => {
          const r1 = 26 + Math.sin(tick * 2 + a) * 1.5;
          const r2 = 32 + Math.sin(tick * 2 + a) * 1.5;
          const x1 = SUN_X + Math.cos(a * Math.PI/180) * r1;
          const y1 = SUN_Y + Math.sin(a * Math.PI/180) * r1;
          const x2 = SUN_X + Math.cos(a * Math.PI/180) * r2;
          const y2 = SUN_Y + Math.sin(a * Math.PI/180) * r2;
          return <line key={a} x1={x1} y1={y1} x2={x2} y2={y2}
                       stroke="#FFC94A" strokeWidth="2.5" strokeLinecap="round"/>;
        })}
        <NodeLabel x={SUN_X} y={SUN_Y + 64} text=""/>
      </g>

      {/* HOUSE — center */}
      <g transform={`translate(${HOUSE_X - 40}, ${HOUSE_Y - 40})`}>
        <ellipse cx="40" cy="92" rx="50" ry="4" fill="rgba(0,0,0,0.12)"/>
        <rect x="5" y="40" width="70" height="50" fill="#F7F3E8" stroke="#E4E0D4" strokeWidth="1"/>
        <polygon points="-5,42 40,8 85,42 75,42 40,18 5,42" fill="url(#roofGrad)"/>
        <polygon points="8,40 38,17 38,30 12,47" fill="url(#panelGrad)" stroke="#00C06F" strokeWidth="0.6"/>
        <polygon points="42,17 72,40 68,47 42,30" fill="url(#panelGrad)" stroke="#00C06F" strokeWidth="0.6"/>
        <polygon points="8,40 38,17 38,30 12,47" fill="#FFE8A0" opacity="0.3"/>
        <polygon points="42,17 72,40 68,47 42,30" fill="#FFE8A0" opacity="0.3"/>
        <rect x="14" y="52" width="18" height="18" fill="#B8D4E8"/>
        <line x1="23" y1="52" x2="23" y2="70" stroke="#8FA8BC" strokeWidth="0.5"/>
        <line x1="14" y1="61" x2="32" y2="61" stroke="#8FA8BC" strokeWidth="0.5"/>
        <rect x="45" y="62" width="14" height="28" fill="#2a3a34"/>
        <circle cx="56" cy="77" r="0.8" fill="#00C06F"/>
      </g>
      <NodeLabel x={HOUSE_X} y={HOUSE_Y + 65} text="YOUR HOME"/>

      {/* GRID — bottom-left, vertically aligned with the community houses */}
      <g transform={`translate(${GRID_X}, ${COMM_Y + 5})`}>
        <rect x="-2" y="-22" width="4" height="44" fill="#6B7370"/>
        <rect x="-18" y="-26" width="36" height="5" rx="0.5" fill="#6B7370"/>
        <rect x="-18" y="-16" width="36" height="5" rx="0.5" fill="#6B7370"/>
        <line x1="-18" y1="-30" x2="-12" y2="-22" stroke="#6B7370" strokeWidth="2"/>
        <line x1="18"  y1="-30" x2="12"  y2="-22" stroke="#6B7370" strokeWidth="2"/>
      </g>
      <NodeLabel x={GRID_X} y={COMM_Y + 50} text="GRID"/>

      {/* COMMUNITY — bottom-right */}
      <g transform={`translate(${COMM_X}, ${COMM_Y})`}>
        {[
          { x: -26, y: 6,  h: 30 },
          { x: 0,   y: -6, h: 38 },
          { x: 26,  y: 8,  h: 28 },
        ].map((c, i) => (
          <g key={i} transform={`translate(${c.x}, ${c.y})`}>
            <rect x="-11" y="-5" width="22" height={c.h} fill="#F7F3E8" stroke="#E4E0D4" strokeWidth="0.8"/>
            <polygon points="-13,-5 0,-16 13,-5" fill="#2a3a34"/>
            <rect x="-4" y="3" width="6" height="7" fill="#FFC94A"
                  opacity={0.6 + 0.3 * Math.sin(tick * 2.5 + i)}/>
          </g>
        ))}
      </g>
      <NodeLabel x={COMM_X} y={COMM_Y + 50} text="COMMUNITY"/>

      {/* FLOWS — sun → home, home → community ONLY */}
      <FlowLine
        path={`M ${SUN_X} ${SUN_Y + 25} Q ${SUN_X} ${HOUSE_Y - 60} ${HOUSE_X} ${HOUSE_Y - 32}`}
        tick={tick} color="#FFB83D" speed={0.7} particles={3} dashed/>
      <FlowLine
        path={`M ${HOUSE_X + 30} ${HOUSE_Y + 30} Q ${HOUSE_X + 65} ${HOUSE_Y + 80} ${COMM_X - 30} ${COMM_Y - 10}`}
        tick={tick} color="#00A862" speed={0.9} particles={4}/>

      {/* IDLE LINK — home ↔ grid: dashed grey, no particles */}
      <path
        d={`M ${HOUSE_X - 30} ${HOUSE_Y + 30} Q ${HOUSE_X - 65} ${HOUSE_Y + 80} ${GRID_X + 22} ${GRID_Y - 18}`}
        fill="none" stroke="#9CA3A0" strokeWidth="1.5"
        strokeDasharray="3 5" strokeOpacity="0.55"/>
    </svg>
  );
}

function NodeLabel({ x, y, text }) {
  return (
    <g>
      <text x={x} y={y} textAnchor="middle"
            fontSize="13" fontFamily="Geist Mono, monospace"
            fill="var(--ink-900)" letterSpacing="0.06em" fontWeight="700">
        {text}
      </text>
    </g>
  );
}

// Animated particle flow along an SVG path using getPointAtLength.
function FlowLine({ path, tick, color, speed = 1, particles = 4, dashed }) {
  const ref = React.useRef();
  const [len, setLen] = React.useState(0);
  React.useEffect(() => {
    if (ref.current) setLen(ref.current.getTotalLength());
  }, [path]);

  const pts = [];
  if (len) {
    for (let i = 0; i < particles; i++) {
      const p = ((tick * speed * 0.22 + i / particles) % 1) * len;
      if (ref.current) {
        const pt = ref.current.getPointAtLength(p);
        pts.push({ x: pt.x, y: pt.y, phase: i / particles });
      }
    }
  }

  return (
    <g>
      <path ref={ref} d={path} fill="none" stroke={color} strokeOpacity="0.3"
            strokeWidth="1.5" strokeDasharray={dashed ? "2 4" : "3 4"}/>
      {pts.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3.5" fill={color}>
          <animate attributeName="opacity" values="0;1;0"
                   dur={`${2/speed}s`} repeatCount="indefinite"
                   begin={`${p.phase * 2/speed}s`}/>
        </circle>
      ))}
    </g>
  );
}

Object.assign(window, { HouseTab });
