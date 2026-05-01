// Screen 1 — Postcode + community
function Screen1_Postcode({ state, setState, onNext }) {
  const [postcode, setPostcode] = React.useState(state.postcode || '');
  const [communityOpen, setCommunityOpen] = React.useState(!!state.communityId);
  const [communityId, setCommunityId] = React.useState(state.communityId || '');
  const [resolved, setResolved] = React.useState(state.postcode ? { area: 'Fulham', neighbors: 47 } : null);
  const [resolving, setResolving] = React.useState(false);
  const [peerInfoOpen, setPeerInfoOpen] = React.useState(false);

  // "Resolve" postcode to area (mock) on valid-looking UK postcode
  const ukLike = /^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d?[A-Z]{0,2}$/i;
  React.useEffect(() => {
    if (ukLike.test(postcode.trim())) {
      setResolving(true);
      const t = setTimeout(() => {
        setResolved({ area: 'Fulham', neighbors: 47 });
        setResolving(false);
      }, 600);
      return () => clearTimeout(t);
    } else {
      setResolved(null);
    }
  }, [postcode]);

  const canContinue = !!resolved && !resolving;

  const handleNext = () => {
    setState(s => ({ ...s, postcode: postcode.toUpperCase(), communityId, area: resolved?.area }));
    onNext();
  };

  return (
    <PwScreen step={0}>
      <div style={{ marginTop: 8, marginBottom: 8 }}>
        <PeerwayLogo size={18}/>
      </div>

      <PwPageTitle
        eyebrow="Step 1 — Your energy community"
        title="Welcome to Peerway, Sarah."
        subtitle="You have been securely redirected from your Octopus online account. Your postcode helps us confirm who you can trade energy with."
        size={34}
      />

      <div style={{ marginTop: 8 }}>
        <label className="t-label" style={{ display: 'block', color: 'var(--ink-400)', marginBottom: 10 }}>
          Postcode
        </label>
        <div style={{ position: 'relative' }}>
          <input
            className="pw-input"
            value={postcode}
            onChange={e => setPostcode(e.target.value)}
            placeholder="e.g. SW6 3JD"
            autoCapitalize="characters"
            style={{ paddingLeft: 48, fontFamily: 'var(--font-sans)', letterSpacing: '0.02em' }}
          />
          <div style={{
            position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)',
            color: 'var(--ink-400)',
          }}>
            <IconPin size={18}/>
          </div>
          {resolving && (
            <div style={{
              position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)',
              width: 16, height: 16, borderRadius: 999,
              border: '2px solid var(--cream-200)', borderTopColor: 'var(--forest-700)',
              animation: 'spin .8s linear infinite',
            }}/>
          )}
        </div>

        {/* Inferred location card */}
        {resolved && !resolving && (
          <div className="pw-fade-in" style={{
            marginTop: 14,
            background: 'var(--lime-50)',
            border: '1px solid var(--lime-100)',
            borderRadius: 'var(--r-md)',
            padding: '14px 16px',
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            {/* Tiny neighbor avatars */}
            <div style={{ display: 'flex' }}>
              {['#2F6B50', '#7FA291', '#1F4A37', '#B8713A'].map((c, i) => (
                <div key={i} style={{
                  width: 24, height: 24, borderRadius: 999, background: c,
                  border: '2px solid var(--cream-50)',
                  marginLeft: i === 0 ? 0 : -8,
                  boxShadow: '0 1px 2px rgba(0,0,0,0.06)',
                }}/>
              ))}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="t-body" style={{ fontSize: 14, color: 'var(--ink-900)', fontWeight: 500 }}>
                Looks like you're in <span style={{ color: 'var(--ink-900)', fontWeight: 600 }}>{resolved.area}</span>
              </div>
              <div className="t-body" style={{ fontSize: 13, color: 'var(--ink-600)', marginTop: 1 }}>
                <span className="t-num" style={{ fontSize: 14, color: 'var(--ink-900)', fontWeight: 600 }}>{resolved.neighbors}</span> neighbors are already trading nearby
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Community ID expandable */}
      <div style={{ marginTop: 20 }}>
        <button onClick={() => setCommunityOpen(o => !o)} style={{
          appearance: 'none', background: 'transparent', border: 0, padding: 0,
          display: 'flex', alignItems: 'center', gap: 6,
          color: 'var(--ink-700)', fontSize: 14, fontFamily: 'var(--font-sans)', fontWeight: 500,
          cursor: 'pointer',
        }}>
          <span>Joining a specific community?</span>
          <div style={{
            transform: `rotate(${communityOpen ? 90 : 0}deg)`,
            transition: 'transform .22s ease',
          }}>
            <IconChevron size={14}/>
          </div>
        </button>
        {communityOpen && (
          <div className="pw-fade-in" style={{ marginTop: 12 }}>
            <input
              className="pw-input"
              value={communityId}
              onChange={e => setCommunityId(e.target.value)}
              placeholder="Community ID (optional)"
              style={{ height: 48, fontSize: 15 }}
            />
          </div>
        )}
      </div>

      {/* What is peer trading? expandable */}
      <div style={{ marginTop: 16 }}>
        <button onClick={() => setPeerInfoOpen(o => !o)} style={{
          appearance: 'none', background: 'transparent', border: 0, padding: 0,
          display: 'inline-flex', alignItems: 'center', gap: 6,
          color: 'var(--ink-700)', fontSize: 14, fontFamily: 'var(--font-sans)',
          fontWeight: 500, cursor: 'pointer',
          borderBottom: '1px dashed var(--ink-400)', paddingBottom: 2,
        }}>
          <span>What is peer trading?</span>
          <div style={{
            transform: `rotate(${peerInfoOpen ? 90 : 0}deg)`,
            transition: 'transform .22s ease',
          }}>
            <IconChevron size={14}/>
          </div>
        </button>
        {peerInfoOpen && (
          <div className="pw-fade-in" style={{
            marginTop: 12, padding: '14px 16px',
            background: 'var(--surface)',
            border: '1px solid var(--cream-200)',
            borderRadius: 'var(--r-md)',
            fontSize: 13, lineHeight: 1.55, color: 'var(--ink-600)',
          }}>
           Peer trading lets you <span style={{ fontWeight: 600, color: 'var(--ink-900)' }}>buy and sell solar electricity directly</span> with your neighbors at cheaper rates. It lowers your bills while creating a cleaner, <span style={{ fontWeight: 600, color: 'var(--ink-900)' }}>more resilient energy grid for everyone</span>. Peerway handles everything <span style={{ fontWeight: 600, color: 'var(--ink-900)' }}>automatically</span> - from optimising your bills to adapting to your household needs.
          </div>
        )}
      </div>

      {/* Primary CTA */}
      <div style={{ marginTop: 40 }}>
        <PwButton onClick={handleNext} disabled={!canContinue} icon={<IconArrowRight size={16}/>}>
          Connect your smart meter
        </PwButton>
        <p style={{
          margin: '14px 4px 0', fontSize: 12, lineHeight: 1.5,
          color: 'var(--ink-400)', display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <IconLock size={12}/>
          We use read-only access via your approved provider.
        </p>
      </div>
    </PwScreen>
  );
}

Object.assign(window, { Screen1_Postcode });
