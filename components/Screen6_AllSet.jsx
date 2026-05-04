// Screen 6 — What happens next
function Screen6_AllSet({ onNext, onBack }) {
  return (
    <PwScreen step={5} onBack={onBack}>
      <PwPageTitle
        eyebrow="Setup complete"
        title="You're all set."
        subtitle="We'll start trading tomorrow. Your first weekly report lands Sunday."
        size={36}
      />

      {/* Projected numbers */}
      <div style={{ marginTop: 24 }}>
        <div className="t-label" style={{ color: 'var(--ink-400)', marginBottom: 12 }}>
          Your first month, projected
        </div>
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-lg)',
          overflow: 'hidden',
        }}>
          {[
            { num: '47',  unit: 'neighbors' },
            { num: '42', unit: 'savings' },
            { num: '32%', unit: 'green mix' },
          ].map((s, i) => (
            <div key={i} style={{
              padding: '18px 12px 16px',
              textAlign: 'center',
              borderLeft: i === 0 ? 0 : '1px solid var(--cream-200)',
            }}>
              <div className="t-num" style={{
                fontSize: 28, color: 'var(--ink-900)', lineHeight: 1,
                letterSpacing: '-0.04em', fontWeight: 600,
              }}>{s.num}</div>
              <div className="t-label" style={{ color: 'var(--ink-400)', marginTop: 8 }}>
                {s.unit}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* What happens next */}
      <div style={{ marginTop: 28 }}>
        <div className="t-label" style={{ color: 'var(--ink-400)', marginBottom: 12 }}>
          What happens next
        </div>
        <div style={{ padding: '0 4px' }}>
          {[
            { when: 'Tonight',           what: 'EV charges during your cheapest overnight window.',         live: true },
            { when: 'Tomorrow, 7am',     what: 'We start routing solar surplus to your neighbors in Fulham.' },
            { when: 'Sunday',            what: 'Your first weekly savings report.' },
          ].map((r, i) => (
            <div key={i} style={{
              display: 'flex', gap: 14, padding: '14px 0',
              borderBottom: i < 2 ? '1px solid var(--cream-200)' : 0,
            }}>
              <div style={{
                width: 28, flexShrink: 0, display: 'flex', flexDirection: 'column',
                alignItems: 'center',
              }}>
                <div style={{
                  width: 10, height: 10, borderRadius: 999,
                  background: r.live ? 'var(--lime-500)' : 'var(--cream-200)',
                  boxShadow: r.live ? '0 0 0 4px rgba(0,192,111,0.20)' : 'none',
                  marginTop: 4,
                }}/>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="t-label" style={{ color: 'var(--ink-400)', marginBottom: 2 }}>
                  {r.when}
                </div>
                <div style={{ fontSize: 14, color: 'var(--ink-900)', lineHeight: 1.45 }}>
                  {r.what}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 32 }}>
        <PwButton onClick={onNext} icon={<IconArrowRight size={16}/>}>
          Open my dashboard
        </PwButton>
      </div>
    </PwScreen>
  );
}

Object.assign(window, { Screen6_AllSet });
