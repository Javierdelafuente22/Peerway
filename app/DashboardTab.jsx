// Dashboard — default landing tab. "Did I save money?"
function DashboardTab() {
  const [window, setWindow] = React.useState('week'); // 'week' | 'month' | 'year'

  const data = {
    week:  { saved: 8.40,  savedTrend: '+12% vs last week', co2: 14.2,  kwh: 38,  pct: 23, benchmark: 'Fulham average', comparisonUp: true },
    month: { saved: 38.20, savedTrend: '+18% vs last month', co2: 62.8,  kwh: 168, pct: 29, benchmark: 'Fulham average', comparisonUp: true },
    year:  { saved: 284.60, savedTrend: 'on track for £440', co2: 540.1, kwh: 1420, pct: 14, benchmark: 'Top of community', comparisonUp: true },
  }[window];

  // Animated count-up for hero £ figure
  const [savedAnim, setSavedAnim] = React.useState(0);
  React.useEffect(() => {
    setSavedAnim(0);
    const target = data.saved;
    const start = performance.now();
    const dur = 650;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setSavedAnim(target * e);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [window]);

  const scrollRef = React.useRef();
  const momentsRef = React.useRef();
  const scrollToMoments = () => {
    if (scrollRef.current && momentsRef.current) {
      const top = momentsRef.current.offsetTop - 60;
      scrollRef.current.scrollTo({ top, behavior: 'smooth' });
    }
  };

  return (
    <div className="pw-screen" ref={scrollRef}>
      <TabHeader
        eyebrow="Dashboard"
        title="Your savings"
        right={
          <button onClick={scrollToMoments} style={{
            appearance: 'none', border: 0, background: 'var(--surface)',
            width: 40, height: 40, borderRadius: 999,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--ink-700)', cursor: 'pointer', position: 'relative',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <IconBell size={16}/>
            <span style={{
              position: 'absolute', top: 9, right: 10,
              width: 6, height: 6, borderRadius: 999, background: 'var(--lime-500)',
              border: '1.5px solid #fff',
            }}/>
          </button>
        }
      />

      <div style={{ padding: '0 24px 120px' }}>
        {/* Time window toggle */}
        <div style={{
          display: 'flex', padding: 4,
          background: 'var(--cream-100)', borderRadius: 999,
          marginBottom: 24,
        }}>
          {['week', 'month', 'year'].map(w => (
            <button key={w} onClick={() => setWindow(w)} style={{
              appearance: 'none', border: 0, cursor: 'pointer',
              flex: 1, height: 36, borderRadius: 999,
              background: window === w ? 'var(--ink-900)' : 'transparent',
              color: window === w ? '#fff' : 'var(--ink-600)',
              fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 500,
              letterSpacing: '-0.005em',
              textTransform: 'capitalize',
              transition: 'all .18s',
            }}>
              This {w}
            </button>
          ))}
        </div>

        {/* Hero — money saved */}
        <div style={{ marginBottom: 28 }}>
          <div className="t-label" style={{ color: 'var(--ink-400)', marginBottom: 10 }}>
            Saved this {window}
          </div>
          <div style={{
            display: 'flex', alignItems: 'baseline', gap: 4,
            color: 'var(--ink-900)',
          }}>
            <span style={{
              fontSize: 32, color: 'var(--ink-400)', fontWeight: 500,
              alignSelf: 'flex-start', marginTop: 10,
            }}>£</span>
            <span className="t-num" style={{
              fontSize: 76, lineHeight: 0.95,
              letterSpacing: '-0.045em', fontWeight: 600,
            }}>
              {savedAnim.toFixed(2)}
            </span>
          </div>
          <div style={{
            marginTop: 10, display: 'flex', alignItems: 'center', gap: 8,
            fontSize: 13, color: 'var(--ink-600)',
          }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              padding: '3px 8px', borderRadius: 999,
              background: 'var(--lime-50)', color: 'var(--lime-600)',
              fontWeight: 600, fontSize: 12,
            }}>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                <path d="M5 1l4 5H6v3H4V6H1l4-5z"/>
              </svg>
              {data.savedTrend}
            </span>
          </div>
        </div>

        {/* Secondary metrics */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20,
        }}>
          <MetricCard icon={<IconLeaf size={14}/>} label="CO₂ saved" value={data.co2.toFixed(1)} unit="kg"/>
          <MetricCard icon={<IconBolt size={12}/>} label="kWh traded" value={data.kwh} unit="kWh"/>
        </div>

        {/* Comparative badge — critical contextual anchor */}
        <div style={{
          padding: '14px 16px', marginBottom: 28,
          background: 'var(--ink-900)', color: '#fff',
          borderRadius: 'var(--r-md)',
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'rgba(0,192,111,0.20)', color: 'var(--lime-400)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <IconSparkle size={16}/>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>
              {data.pct}% better than {data.benchmark}
            </div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', marginTop: 1 }}>
              You're in the top 30% of your community
            </div>
          </div>
          <button style={{
            appearance: 'none', border: 0, background: 'transparent',
            color: 'rgba(255,255,255,0.5)', cursor: 'pointer',
          }}>
            <IconChevron size={14}/>
          </button>
        </div>

        {/* Insights feed */}
        <div ref={momentsRef} style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 12,
          scrollMarginTop: 80,
        }}>
          <h2 style={{
            fontSize: 14, margin: 0,
            color: 'var(--ink-900)', fontWeight: 600,
            letterSpacing: '-0.01em',
          }}>
            This week's moments
          </h2>
          <span className="t-mono" style={{ color: 'var(--ink-400)', fontSize: 11 }}>
            4 new
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <InsightCard
            day="Thu"
            icon="☀️"
            title="Your solar powered the kettles at St. Mary's Primary this morning"
            detail="7.2 kWh sent at 10:45am"
            accent="lime"
          />
          <InsightCard
            day="Wed"
            icon="🌧"
            title="Quiet week — rainy, but you still saved £2.20 vs. standard tariff"
            detail="Battery covered 68% of evening peak"
            accent="neutral"
          />
          <InsightCard
            day="Tue"
            icon="🏘"
            title="You traded with 3 homes and a farm today"
            detail="9.5 kWh sent at noon while you were away"
            accent="lime"
          />
          <InsightCard
            day="Mon"
            icon="⚡"
            title="Peak shift: EV charged 2am–5am, saved £0.84"
            detail="Took advantage of a cheap rate window"
            accent="neutral"
          />
        </div>

        {/* Footer trust anchor */}
        <div style={{
          marginTop: 24, padding: '12px 14px',
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-md)',
          display: 'flex', alignItems: 'center', gap: 10,
          fontSize: 12, color: 'var(--ink-600)',
        }}>
          <IconShield size={14}/>
          <span style={{ flex: 1 }}>
            You're never worse off than your standard tariff.
          </span>
          <IconInfo size={14}/>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, unit }) {
  return (
    <div style={{
      padding: '14px 16px',
      background: 'var(--surface)',
      border: '1px solid var(--cream-200)',
      borderRadius: 'var(--r-md)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        color: 'var(--ink-400)', marginBottom: 8,
      }}>
        {icon}
        <span className="t-label">{label}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span className="t-num" style={{
          fontSize: 26, color: 'var(--ink-900)', fontWeight: 600,
          letterSpacing: '-0.035em',
        }}>{value}</span>
        <span style={{ fontSize: 12, color: 'var(--ink-400)', fontWeight: 500 }}>{unit}</span>
      </div>
    </div>
  );
}

function InsightCard({ day, icon, title, detail, accent }) {
  return (
    <div style={{
      padding: 14,
      background: 'var(--surface)',
      border: '1px solid var(--cream-200)',
      borderRadius: 'var(--r-md)',
      display: 'flex', gap: 12, alignItems: 'flex-start',
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: 10,
        background: accent === 'lime' ? 'var(--lime-50)' : 'var(--cream-100)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 20, flexShrink: 0,
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3,
        }}>
          <span className="t-label" style={{ color: 'var(--ink-400)' }}>{day}</span>
          {accent === 'lime' && (
            <span style={{
              width: 4, height: 4, borderRadius: 999,
              background: 'var(--lime-500)',
            }}/>
          )}
        </div>
        <div style={{
          fontSize: 14, color: 'var(--ink-900)',
          lineHeight: 1.4, fontWeight: 500, letterSpacing: '-0.005em',
          marginBottom: 4, textWrap: 'pretty',
        }}>
          {title}
        </div>
        <div style={{
          fontSize: 12, color: 'var(--ink-600)', lineHeight: 1.4,
        }}>
          {detail}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DashboardTab });
