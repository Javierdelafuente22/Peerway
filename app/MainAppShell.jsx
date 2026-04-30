// Clean main-app shell — 5-tab app.
// On mobile (touch + narrow screen), renders full-screen with no frame.
// On desktop, keeps the centered IOSDevice card.

function MainAppShell() {
  const [tab, setTab] = React.useState('dashboard');

  const isMobile =
    window.matchMedia('(max-width: 600px) and (pointer: coarse)').matches ||
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

  if (isMobile) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'var(--cream-50, #F4F5F2)',
        overflow: 'hidden',
      }}>
        {content}
      </div>
    );
  }

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
