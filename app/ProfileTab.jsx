// Profile tab — account management
function ProfileTab() {
  const [paused, setPaused] = React.useState(false);
  const [digest, setDigest] = React.useState(true);
  const [goodDay, setGoodDay] = React.useState(true);
  const [delConfirm, setDelConfirm] = React.useState(0); // 0 | 1 | 2

  return (
    <div className="pw-screen">
      <TabHeader eyebrow="Profile" title="Account & data"/>

      <div style={{ padding: '0 24px 120px' }}>
        {/* User card */}
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-md)',
          overflow: 'hidden',
          marginBottom: 20,
        }}>
          <div style={{
            background: 'var(--lime-50)',
            padding: '18px 18px 16px',
            color: 'var(--ink-900)',
            display: 'flex', alignItems: 'center', gap: 14,
            borderBottom: '1px solid var(--lime-100)',
          }}>
            <div style={{
              width: 44, height: 44, borderRadius: 999,
              background: 'var(--lime-500)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--ink-900)', fontWeight: 600, fontSize: 16,
            }}>SC</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--ink-900)', letterSpacing: '-0.005em' }}>Sarah Chen</div>
              <div style={{ fontSize: 12, color: 'var(--ink-600)' }}>
                SW6 3JD · Fulham · Member since Apr 2026
              </div>
            </div>
            <div style={{
              padding: '4px 8px', borderRadius: 999,
              background: 'var(--ink-900)',
              color: 'var(--lime-400)',
              fontSize: 11, letterSpacing: '0.05em',
              textTransform: 'uppercase',
              fontWeight: 600,
            }}>
              Prosumer
            </div>
          </div>
          <ProfileRow icon={<IconHome size={14}/>} label="Household"    value="2 adults, 1 EV"/>
          <ProfileRow icon={<IconSolar size={14}/>} label="Solar"        value="4.2kW array · Fronius" last/>
        </div>

        {/* Trading status */}
        <SectionLabel>Trading</SectionLabel>
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-md)',
          overflow: 'hidden',
          marginBottom: 20,
        }}>
          <ConnectionRow
            title="Smart meter"
            subtitle="Octopus Energy · IHD-5B62"
            status="connected"
          />
          <ConnectionRow
            title="Tariff"
            subtitle="Octopus Agile · Variable · £0.24/kWh avg"
            status="info"
            last={!paused}
          />
          {/* Pause toggle */}
          <div style={{
            borderTop: '1px solid var(--cream-200)',
            padding: '14px 18px',
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <div style={{
              width: 34, height: 34, borderRadius: 10,
              background: paused ? 'var(--cream-100)' : 'var(--lime-50)',
              color: paused ? 'var(--ink-600)' : 'var(--lime-600)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <IconPause size={12}/>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, color: 'var(--ink-900)', fontWeight: 500, letterSpacing: '-0.005em' }}>
                {paused ? 'Trading paused' : 'Actively trading'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--ink-600)', marginTop: 1 }}>
                {paused ? 'You\'ll use the grid as normal' : 'Your surplus is being sold to peers'}
              </div>
            </div>
            <Toggle on={!paused} onChange={v => setPaused(!v)}/>
          </div>
        </div>

        {/* Notifications */}
        <SectionLabel>Notifications</SectionLabel>
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-md)',
          overflow: 'hidden',
          marginBottom: 20,
        }}>
          <ToggleRow
            icon="📩"
            title="Weekly digest"
            detail="Sunday, 8am — what you saved last week"
            on={digest} onChange={setDigest}
          />
          <ToggleRow
            icon="☀️"
            title="Good day alerts"
            detail="Push when you crack your own savings record"
            on={goodDay} onChange={setGoodDay}
            last
          />
        </div>

        {/* Data rights */}
        <SectionLabel>Your data (GDPR)</SectionLabel>
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-md)',
          overflow: 'hidden',
          marginBottom: 20,
        }}>
          <LinkRow icon={<IconDownload size={14}/>} title="Export my data" detail="Download everything as JSON"/>
          <LinkRow icon={<IconPencil size={14}/>}   title="Rectify my data" detail="Fix something that's wrong"/>
          <LinkRow icon={<IconLock size={14}/>}     title="Withdraw consent" detail="Revoke specific permissions"
                   last/>
        </div>

        {/* Support */}
        <SectionLabel>Support</SectionLabel>
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-md)',
          overflow: 'hidden',
          marginBottom: 20,
        }}>
          <LinkRow icon={<IconDoc size={14}/>} title="Help centre" detail="Guides, FAQs, troubleshooting"/>
          <LinkRow icon={<IconExternal size={12}/>} title="Contact support" detail="Real humans · reply within 4h"
                   last/>
        </div>

        {/* Danger zone */}
        <SectionLabel danger>Danger zone</SectionLabel>
        <div style={{
          background: 'var(--surface)',
          border: '1px solid ' + (delConfirm > 0 ? '#D4524B' : 'var(--cream-200)'),
          borderRadius: 'var(--r-md)',
          padding: 16, transition: 'border-color .2s',
        }}>
          <div style={{
            fontSize: 14, color: 'var(--ink-900)', fontWeight: 600,
            marginBottom: 4, letterSpacing: '-0.005em',
          }}>
            Delete my account
          </div>
          <div style={{
            fontSize: 12, color: 'var(--ink-600)',
            lineHeight: 1.5, marginBottom: 14, textWrap: 'pretty',
          }}>
            {delConfirm === 0 && 'Trading stops, your data is erased within 30 days, and your community share is reallocated. This cannot be undone.'}
            {delConfirm === 1 && 'Really sure? Trading will end and your account will be deleted. Tap again to confirm.'}
            {delConfirm === 2 && 'Request submitted. Your account will be deleted within 30 days. We\'ve sent an email.'}
          </div>
          {delConfirm < 2 ? (
            <button onClick={() => setDelConfirm(delConfirm + 1)} style={{
              appearance: 'none', border: '1px solid #D4524B',
              background: delConfirm === 1 ? '#D4524B' : 'transparent',
              color: delConfirm === 1 ? '#fff' : '#D4524B',
              padding: '10px 14px', borderRadius: 10,
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              letterSpacing: '-0.005em',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <IconTrash size={12}/>
              {delConfirm === 0 ? 'Delete my account' : 'Yes, delete everything'}
            </button>
          ) : (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '6px 10px', borderRadius: 8,
              background: 'var(--cream-100)', color: 'var(--ink-700)',
              fontSize: 11, fontWeight: 600, letterSpacing: '0.02em',
              fontFamily: 'var(--font-mono)',
            }}>
              <IconCheck size={12}/>
              REQUEST RECEIVED
            </div>
          )}
        </div>

        {/* Meta footer */}
        <div style={{
          marginTop: 24, fontSize: 10,
          color: 'var(--ink-400)',
          textAlign: 'center',
          fontFamily: 'var(--font-mono)',
          letterSpacing: '0.05em',
        }}>
          PEERWAY v2.4.1 · BUILD 2026.04.19
        </div>
      </div>
    </div>
  );
}

function SectionLabel({ children, danger }) {
  return (
    <div className="t-label" style={{
      color: danger ? '#D4524B' : 'var(--ink-400)',
      marginBottom: 8, marginTop: 4,
      padding: '0 4px',
    }}>
      {children}
    </div>
  );
}

function ProfileRow({ icon, label, value, last }) {
  return (
    <div style={{
      padding: '14px 18px',
      display: 'flex', alignItems: 'center', gap: 12,
      borderTop: '1px solid var(--cream-200)',
      borderBottom: last ? 0 : 0,
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: 8,
        background: 'var(--cream-100)', color: 'var(--ink-600)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="t-label" style={{ color: 'var(--ink-400)', marginBottom: 2 }}>
          {label}
        </div>
        <div style={{ fontSize: 14, color: 'var(--ink-900)', fontWeight: 500, letterSpacing: '-0.005em' }}>
          {value}
        </div>
      </div>
      <button style={{
        appearance: 'none', border: 0, background: 'transparent',
        color: 'var(--ink-400)', cursor: 'pointer',
      }}>
        <IconPencil size={12}/>
      </button>
    </div>
  );
}

function ConnectionRow({ title, subtitle, status, last }) {
  const dot = status === 'connected' ? 'var(--lime-500)' : 'var(--ink-400)';
  return (
    <div style={{
      padding: '14px 18px',
      display: 'flex', alignItems: 'center', gap: 12,
      borderBottom: last ? 0 : '1px solid var(--cream-200)',
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
          <span style={{
            width: 6, height: 6, borderRadius: 999, background: dot,
          }}/>
          <span className="t-label" style={{ color: 'var(--ink-400)' }}>{title}</span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--ink-900)', fontWeight: 500, letterSpacing: '-0.005em' }}>
          {subtitle}
        </div>
      </div>
      <button style={{
        appearance: 'none', border: 0, background: 'transparent',
        color: 'var(--ink-400)', cursor: 'pointer',
      }}>
        <IconChevron size={14}/>
      </button>
    </div>
  );
}

function ToggleRow({ icon, title, detail, on, onChange, last }) {
  return (
    <div style={{
      padding: '14px 18px',
      display: 'flex', alignItems: 'center', gap: 12,
      borderBottom: last ? 0 : '1px solid var(--cream-200)',
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: 10,
        background: 'var(--cream-100)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 14, flexShrink: 0,
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, color: 'var(--ink-900)', fontWeight: 500, letterSpacing: '-0.005em' }}>
          {title}
        </div>
        <div style={{ fontSize: 12, color: 'var(--ink-600)', marginTop: 1 }}>
          {detail}
        </div>
      </div>
      <Toggle on={on} onChange={onChange}/>
    </div>
  );
}

function LinkRow({ icon, title, detail, last }) {
  return (
    <button style={{
      appearance: 'none', border: 0, background: 'transparent',
      width: '100%', padding: '14px 18px',
      display: 'flex', alignItems: 'center', gap: 12,
      textAlign: 'left', cursor: 'pointer',
      borderBottom: last ? 0 : '1px solid var(--cream-200)',
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: 10,
        background: 'var(--cream-100)', color: 'var(--ink-600)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, color: 'var(--ink-900)', fontWeight: 500, letterSpacing: '-0.005em' }}>
          {title}
        </div>
        <div style={{ fontSize: 12, color: 'var(--ink-600)', marginTop: 1 }}>
          {detail}
        </div>
      </div>
      <IconChevron size={14}/>
    </button>
  );
}

function Toggle({ on, onChange }) {
  return (
    <button onClick={() => onChange(!on)} style={{
      appearance: 'none', border: 0, cursor: 'pointer',
      width: 42, height: 24, borderRadius: 999,
      background: on ? 'var(--lime-500)' : 'var(--cream-200)',
      position: 'relative', flexShrink: 0,
      transition: 'background .18s',
    }}>
      <div style={{
        position: 'absolute', top: 2, left: on ? 20 : 2,
        width: 20, height: 20, borderRadius: 999,
        background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        transition: 'left .18s',
      }}/>
    </button>
  );
}

Object.assign(window, { ProfileTab });
