// Screen 5 — Legal + consent
function Screen5_Legal({ onNext, onBack }) {
  const [agreed, setAgreed] = React.useState(false);

  const items = [
    { label: 'Terms of Service',    desc: 'How Peerway operates and what you agree to.',                icon: <IconDoc size={14}/> },
    { label: 'Your data',           desc: "What we collect, why, and where it's stored (EU-only).",     icon: <IconShield size={14}/> },
    { label: 'Right to erasure',    desc: 'Delete everything at any time, no questions asked.',         icon: <IconTrash size={14}/> },
    { label: 'Right to portability',desc: 'Export your full trading history in one click.',             icon: <IconDownload size={14}/> },
  ];

  return (
    <PwScreen step={4} onBack={onBack}>
      <PwPageTitle
        eyebrow="Step 4 — Consent"
        title="Terms, in plain English."
        subtitle="The short version is below. Tap any line for the full text."
        size={32}
      />

      {/* Reassurance — pinned above the list as the most important thing */}
      <div style={{ marginTop: 4 }}>
        <PwReassurance title="Why Peerway saves you money.">
          Trading directly with peers means you buy for less and sell for more than you would on the standard grid tariff.
        </PwReassurance>
      </div>

      {/* List of legal items */}
      <div className="pw-card" style={{ marginTop: 20, overflow: 'hidden' }}>
        {items.map((it, i) => (
          <button key={i} style={{
            appearance: 'none', border: 0, background: 'transparent',
            width: '100%', textAlign: 'left', cursor: 'pointer',
            padding: '14px 18px',
            display: 'flex', alignItems: 'flex-start', gap: 12,
            borderTop: i === 0 ? 0 : '1px solid var(--cream-200)',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: 'var(--lime-50)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--ink-900)', flexShrink: 0, marginTop: 2,
            }}>{it.icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 15, color: 'var(--ink-900)', fontWeight: 500 }}>
                {it.label}
              </div>
              <div style={{ fontSize: 13, color: 'var(--ink-600)', marginTop: 2, lineHeight: 1.4 }}>
                {it.desc}
              </div>
            </div>
            <div style={{ color: 'var(--ink-400)', marginTop: 4, flexShrink: 0 }}>
              <IconChevron size={14}/>
            </div>
          </button>
        ))}
      </div>

      {/* Consent checkbox — single handler on the wrapping button */}
      <button
        type="button"
        onClick={() => setAgreed(a => !a)}
        style={{
          appearance: 'none', width: '100%', textAlign: 'left', cursor: 'pointer',
          marginTop: 20, display: 'flex', gap: 12, alignItems: 'flex-start',
          padding: '14px 16px',
          background: agreed ? 'var(--lime-50)' : 'var(--surface)',
          border: `1px solid ${agreed ? 'var(--lime-500)' : 'var(--cream-200)'}`,
          borderRadius: 'var(--r-md)',
          transition: 'background .18s, border-color .18s',
          fontFamily: 'var(--font-sans)',
        }}>
        <div style={{
          width: 22, height: 22, borderRadius: 6,
          border: `1.5px solid ${agreed ? 'var(--ink-900)' : 'var(--ink-300)'}`,
          background: agreed ? 'var(--ink-900)' : 'transparent',
          flexShrink: 0, marginTop: 1,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all .16s',
        }}>
          {agreed && <span style={{ color: 'var(--lime-400)', display: 'flex' }}><IconCheck size={14}/></span>}
        </div>
        <span style={{ fontSize: 14, lineHeight: 1.5, color: 'var(--ink-700)' }}>
          I agree to Peerway's Terms and Privacy policy, and consent to automated trading on my behalf.
        </span>
      </button>

      <div style={{ marginTop: 20 }}>
        <PwButton onClick={onNext} disabled={!agreed} icon={<IconArrowRight size={16}/>}>
          Accept & continue
        </PwButton>
      </div>
    </PwScreen>
  );
}

Object.assign(window, { Screen5_Legal });
