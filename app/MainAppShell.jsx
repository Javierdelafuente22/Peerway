// Clean main-app shell — 5-tab app.
// In PWA/standalone mode (home screen icon), renders full-screen with no frame.
// In a browser window (desktop preview), keeps the centered IOSDevice card.

function MainAppShell() {
  const [tab, setTab] = React.useState('dashboard');

  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  const renderTab = () => {
    switch (tab) {
      case 'home':      return <HouseTab/>;
      case 'community': return <CommunityTab/>;
      case 'dashboard': return <DashboardTab/>;
      case 'assistant': return <AssistantTab/>;
      case 'profile':   return <ProfileTab/>;
      default:          return <DashboardTab/>;
    }
  };

  const content = (
    <div key={tab} style={{ height: '100%', position: 'relative' }} className="pw-fade-in">
      {renderTab()}
      <TabBar active={tab} onChange={setTab}/>
    </div>
  );

  // PWA / standalone → full-screen, no frame, no extra padding
  if (isStandalone) {
    return (
      <div style={{
        width: '100%',
        height: '100vh',
        height: '100svh',
        background: 'var(--cream-50, #F4F5F2)',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {content}
      </div>
    );
  }

  // Desktop / in-browser → centered device frame
  return (
    <div style={{
      minHeight: '100vh', background: '#E8E3D6',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px', boxSizing: 'border-box',
    }}>
      <IOSDevice width={390} height={844}>
        {content}
      </IOSDevice>
    </div>
  );
}

Object.assign(window, { MainAppShell });
