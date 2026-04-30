// Community tab — animated map of anonymized trading peers
function CommunityTab() {
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

  return (
    <div className="pw-screen">
      <TabHeader
        eyebrow="Community"
        title="Your peers"
        subtitle="Anonymised peers trading within 0.8 miles of you." />
      

      <div style={{ padding: '0 0 120px' }}>
        {/* Map canvas */}
        <div style={{
          margin: '0 16px',
          height: 300, position: 'relative',
          borderRadius: 'var(--r-lg)',
          background: 'linear-gradient(180deg, #EEF4E8 0%, #E4EEDC 100%)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <CommunityMap tick={tick} />

          {/* Legend */}
          <div style={{
            position: 'absolute', top: 14, left: 14,
            padding: '8px 10px',
            background: 'rgba(255,255,255,0.85)',
            backdropFilter: 'blur(6px)',
            WebkitBackdropFilter: 'blur(6px)',
            borderRadius: 10,
            display: 'flex', flexDirection: 'column', gap: 4,
            fontSize: 10, fontFamily: 'var(--font-mono)',
            color: 'var(--ink-700)', letterSpacing: '0.02em'
          }}>
            <LegendItem color="var(--lime-500)" label="YOU" />
            <LegendItem color="var(--ink-900)" label="PEER" />
            <LegendItem color="#6B7370" label="GRID" />
          </div>

          {/* Live count */}
          <div style={{
            position: 'absolute', top: 14, right: 14,
            padding: '6px 10px', background: 'var(--ink-900)', color: '#fff',
            borderRadius: 999, display: 'flex', alignItems: 'center', gap: 6,
            fontSize: 11, fontFamily: 'var(--font-mono)', letterSpacing: '0.02em'
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: 999, background: 'var(--lime-400)',
              animation: 'pwPulse 1.4s ease-in-out infinite'
            }} />
            <span>LIVE · 7 TRADES/MIN</span>
          </div>
        </div>

        {/* Collective impact */}
        <div style={{ padding: '24px 24px 0' }}>
          <div style={{
            padding: 18,
            background: 'var(--ink-900)',
            color: '#fff',
            borderRadius: 'var(--r-lg)',
            position: 'relative', overflow: 'hidden'
          }}>
            <div className="t-label" style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 8 }}>
              Collective impact this month
            </div>
            <div style={{
              display: 'flex', alignItems: 'baseline', gap: 6,
              marginBottom: 6
            }}>
              <span className="t-num" style={{
                fontSize: 36, lineHeight: 1, color: '#fff',
                letterSpacing: '-0.04em', fontWeight: 600
              }}>12</span>
              <span style={{ fontSize: 16, color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>kg CO2 offset</span>
            </div>
            <div style={{
              fontSize: 13, color: 'rgba(255,255,255,0.75)',
              lineHeight: 1.4, textWrap: 'pretty'
            }}>
              Equivalent to a <span style={{ color: 'var(--lime-400)', fontWeight: 600 }}>London → Edinburgh</span> train trip — for the whole community.
            </div>

            {/* Decorative sparkline */}
            <svg viewBox="0 0 120 30" width="120" height="30"
            style={{ position: 'absolute', right: 16, top: 16, opacity: 0.35 }}>
              <path d="M0,22 L15,18 L30,14 L45,18 L60,10 L75,14 L90,6 L105,9 L120,4"
              fill="none" stroke="var(--lime-400)" strokeWidth="1.5"
              strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        </div>

        {/* Trading breakdown */}
        <div style={{ padding: '20px 24px 0' }}>
          <div className="t-label" style={{ color: 'var(--ink-400)', marginBottom: 12 }}>
            This month you've traded with
          </div>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10
          }}>
            <BreakdownTile n="3" label="Homes" emoji="🏠" />
            <BreakdownTile n="1" label="School" emoji="🎓" />
            <BreakdownTile n="2" label="Shops" emoji="🛍" />
          </div>
        </div>

        {/* Community composition */}
        <div style={{ padding: '20px 24px 0' }}>
          <div style={{
            padding: 16,
            background: 'var(--surface)',
            border: '1px solid var(--cream-200)',
            borderRadius: 'var(--r-md)'
          }}>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              marginBottom: 12, alignItems: 'baseline'
            }}>
              <span className="t-label" style={{ color: 'var(--ink-400)' }}>
                Community composition
              </span>
              <span style={{ fontSize: 11, color: 'var(--ink-600)', fontFamily: 'var(--font-mono)' }}>
                47 members
              </span>
            </div>
            <div style={{ display: 'flex', height: 8, borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ flex: 24, background: 'var(--lime-500)' }} />
              <div style={{ flex: 12, background: 'var(--forest-700)' }} />
              <div style={{ flex: 8, background: '#3a5a4a' }} />
              <div style={{ flex: 3, background: 'var(--cream-200)' }} />
            </div>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              fontSize: 11, color: 'var(--ink-600)', marginTop: 10,
              flexWrap: 'wrap', gap: 8
            }}>
              <Swatch color="var(--lime-500)" label="Prosumers 24" />
              <Swatch color="var(--forest-700)" label="Consumers 12" />
              <Swatch color="#3a5a4a" label="Shops 8" />
              <Swatch color="var(--cream-200)" label="School 3" />
            </div>
          </div>
        </div>

        {/* Invite CTA — at the bottom */}
        <div style={{ padding: '24px 24px 0' }}>
          <button className="pw-btn pw-btn-primary" style={{
            width: '100%', height: 56,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '0 20px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 999,
                background: 'rgba(0,192,111,0.20)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--lime-400)'
              }}>
                <IconPlus size={14} />
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>Invite a neighbor</div>
                <div style={{
                  fontSize: 11, color: 'rgba(255,255,255,0.6)', fontWeight: 500,
                  letterSpacing: '-0.005em', marginTop: 1
                }}>
                  You both earn £10 when they join
                </div>
              </div>
            </div>
            <IconChevron size={16} />
          </button>
        </div>
      </div>
    </div>);

}

function LegendItem({ color, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 8, height: 8, borderRadius: 2, background: color }} />
      <span>{label}</span>
    </div>);

}

function BreakdownTile({ n, label, emoji }) {
  return (
    <div style={{
      padding: 12,
      background: 'var(--surface)',
      border: '1px solid var(--cream-200)',
      borderRadius: 'var(--r-md)',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: 20, marginBottom: 4 }}>{emoji}</div>
      <div className="t-num" style={{
        fontSize: 22, color: 'var(--ink-900)', fontWeight: 600,
        letterSpacing: '-0.03em', lineHeight: 1
      }}>{n}</div>
      <div style={{
        fontSize: 11, color: 'var(--ink-600)', marginTop: 4,
        letterSpacing: '-0.005em'
      }}>{label}</div>
    </div>);

}

function Swatch({ color, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{ width: 8, height: 8, borderRadius: 2, background: color }} />
      {label}
    </span>);

}

// Animated map with anonymized nodes. 10 peers + grid node + you.
// Positions are stable, flows are randomized per tick to feel alive.
const PEERS = [
{ x: 72, y: 92, type: 'home' },
{ x: 130, y: 70, type: 'home' },
{ x: 200, y: 84, type: 'shop' },
{ x: 268, y: 106, type: 'home' },
{ x: 320, y: 156, type: 'school' },
{ x: 295, y: 246, type: 'home' },
{ x: 230, y: 270, type: 'shop' },
{ x: 150, y: 260, type: 'home' },
{ x: 80, y: 234, type: 'home' },
{ x: 48, y: 174, type: 'home' }];

const GRID_NODE = { x: 220, y: 185 };
const YOU_NODE = { x: 140, y: 160 };

function CommunityMap({ tick }) {
  // Active flows — fixed set so the visualization is stable, not constantly reshuffling
  const activeFlows = React.useMemo(() => {
    return [
      { from: YOU_NODE,  to: PEERS[1], color: '#00C06F' },  // YOU → home (NW-ish)
      { from: PEERS[6], to: YOU_NODE,  color: '#00A862' },  // shop → YOU
      { from: PEERS[4], to: GRID_NODE, color: '#8aa69b' },  // school → GRID
      { from: PEERS[8], to: PEERS[2],  color: '#00A862' },  // home → shop (peer↔peer)
    ];
  }, []);

  return (
    <svg viewBox="0 0 360 295" style={{ width: '100%', height: '100%', display: 'block' }}>
      <defs>
        <radialGradient id="youGlow" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="#00C06F" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#00C06F" stopOpacity="0" />
        </radialGradient>
        <pattern id="mapGrid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,168,98,0.08)" strokeWidth="0.5" />
        </pattern>
      </defs>

      {/* Subtle map grid */}
      <rect width="360" height="295" fill="url(#mapGrid)" />

      {/* Stylized 'roads' — soft organic lines */}
      <path d="M -20 180 Q 100 160 200 175 T 380 160"
      fill="none" stroke="rgba(0,168,98,0.10)" strokeWidth="18" strokeLinecap="round" />
      <path d="M 180 -20 Q 195 100 190 180 T 210 360"
      fill="none" stroke="rgba(0,168,98,0.10)" strokeWidth="14" strokeLinecap="round" />

      {/* Soft 'neighborhood blob' */}
      <path d="M 40 120 Q 60 60 180 70 Q 320 60 330 180 Q 340 280 180 290 Q 40 300 30 180 Z"
      fill="rgba(0,168,98,0.04)" stroke="rgba(0,168,98,0.15)"
      strokeWidth="1" strokeDasharray="3 5" />

      {/* Connections — all peers to grid node, faint */}
      {PEERS.map((p, i) =>
      <line key={`c${i}`} x1={p.x} y1={p.y} x2={GRID_NODE.x} y2={GRID_NODE.y}
      stroke="rgba(14,42,31,0.08)" strokeWidth="0.8" />
      )}

      {/* Flows animated */}
      {activeFlows.map((f, i) =>
      <AnimatedFlow key={i} from={f.from} to={f.to} color={f.color} tick={tick} delay={i * 0.3} />
      )}

      {/* Grid node */}
      <g transform={`translate(${GRID_NODE.x}, ${GRID_NODE.y})`}>
        <circle r="22" fill="#fff" stroke="#6B7370" strokeWidth="1.4" />
        <g transform="translate(-12, -12)" color="#6B7370">
          <IconGrid size={24} />
        </g>
      </g>

      {/* Peer houses */}
      {PEERS.map((p, i) =>
      <PeerNode key={i} x={p.x} y={p.y} type={p.type} pulse={0.6 + 0.4 * Math.sin(tick * 2 + i)} />
      )}

      {/* YOU — pulsing center */}
      <g transform={`translate(${YOU_NODE.x}, ${YOU_NODE.y})`}>
        <circle r={30 + Math.sin(tick * 2) * 2} fill="url(#youGlow)" />
        <circle r="19" fill="var(--lime-500)" stroke="#fff" strokeWidth="2" />
        <text x="0" y="4" textAnchor="middle" fontSize="10" fontFamily="Geist Mono, monospace"
        fill="var(--ink-900)" fontWeight="700" letterSpacing="0.05em">
          YOU
        </text>
      </g>
    </svg>);

}

function PeerNode({ x, y, type, pulse }) {
  const emoji = { home: '🏠', shop: '🛍', school: '🎓' }[type];
  return (
    <g transform={`translate(${x}, ${y})`}>
      <circle r="16" fill="var(--ink-900)" opacity={0.9} />
      <circle r="16" fill="none" stroke="var(--lime-400)" strokeWidth="1" opacity={pulse * 0.5} />
      <text x="0" y="5" textAnchor="middle" fontSize="15">{emoji}</text>
    </g>);

}

function AnimatedFlow({ from, to, color, tick, delay = 0 }) {
  const ref = React.useRef();
  const [len, setLen] = React.useState(0);
  React.useEffect(() => {
    if (ref.current) setLen(ref.current.getTotalLength());
  }, [from, to]);

  // Curved path for more organic feel
  const mx = (from.x + to.x) / 2;
  const my = (from.y + to.y) / 2;
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const curve = dist * 0.2;
  const nx = -dy / dist * curve;
  const ny = dx / dist * curve;
  const d = `M ${from.x} ${from.y} Q ${mx + nx} ${my + ny} ${to.x} ${to.y}`;

  const pts = [];
  if (len) {
    for (let i = 0; i < 3; i++) {
      const p = ((tick + delay) * 0.22 + i / 3) % 1 * len;
      if (ref.current) {
        const pt = ref.current.getPointAtLength(p);
        pts.push({ x: pt.x, y: pt.y });
      }
    }
  }

  return (
    <g>
      <path ref={ref} d={d} fill="none" stroke={color} strokeOpacity="0.22" strokeWidth="1" strokeDasharray="2 3" />
      {pts.map((p, i) =>
      <circle key={i} cx={p.x} cy={p.y} r={2.5} fill={color}>
          <animate attributeName="opacity" values="0;1;0" dur="4.5s" repeatCount="indefinite" begin={`${i * 1.5}s`} />
        </circle>
      )}
    </g>);

}

Object.assign(window, { CommunityTab });