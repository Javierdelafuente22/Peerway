// Print-only shell — renders all 5 tabs as separate pages for PDF export.
function PeerwayPrintShell() {
  const tabs = [
    { id: 'home',      label: 'Home',      sub: 'Live energy flow',          render: () => <HouseTab/> },
    { id: 'community', label: 'Community', sub: 'Anonymised trading map',    render: () => <CommunityTab/> },
    { id: 'dashboard', label: 'Dashboard', sub: 'Savings check-in',          render: () => <DashboardTab/> },
    { id: 'assistant', label: 'Assistant', sub: 'AI trading agent',          render: () => <AssistantTab/> },
    { id: 'profile',   label: 'Profile',   sub: 'Account & data',            render: () => <ProfileTab/> },
  ];

  return (
    <div className="print-doc">
      {/* Cover page */}
      <section className="print-page print-cover">
        <div className="cover-mark">
          <svg width="56" height="56" viewBox="0 0 100 100">
            <rect width="100" height="100" rx="22" fill="#07160F"/>
            <circle cx="50" cy="50" r="20" fill="#00C06F"/>
            <path d="M52 34 L40 54 L48 54 L44 66 L60 46 L52 46 Z" fill="#07160F"/>
          </svg>
          <div className="cover-wordmark">Peerway</div>
        </div>
        <h1 className="cover-title">P2P Energy Management</h1>
        <p className="cover-sub">Mobile app · 5 core tabs · interactive prototype</p>
        <div className="cover-meta">
          <div><span className="meta-k">Tabs</span><span className="meta-v">Home · Community · Dashboard · Assistant · Profile</span></div>
          <div><span className="meta-k">Platform</span><span className="meta-v">iOS · 390×844pt</span></div>
          <div><span className="meta-k">Type system</span><span className="meta-v">Geist · Geist Mono</span></div>
        </div>
        <div className="cover-foot">peerway.app</div>
      </section>

      {/* One page per tab */}
      {tabs.map((t, i) => (
        <section key={t.id} className="print-page">
          <header className="page-header">
            <div className="page-eyebrow">{String(i + 1).padStart(2, '0')} · {t.label}</div>
            <div className="page-title">{t.sub}</div>
          </header>
          <div className="phone-stage">
            <IOSDevice width={390} height={844}>
              <div style={{ height: '100%', position: 'relative' }}>
                {t.render()}
                <TabBar active={t.id} onChange={() => {}}/>
              </div>
            </IOSDevice>
          </div>
          <footer className="page-footer">
            <span>Peerway · {t.label}</span>
            <span>{i + 2} / {tabs.length + 1}</span>
          </footer>
        </section>
      ))}
    </div>
  );
}

Object.assign(window, { PeerwayPrintShell });
