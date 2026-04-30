// Clean main-app shell — no rails, no tweaks, no debug labels.
// 5-tab app inside an iOS device frame. Always lands on dashboard first.

function MainAppShell() {
  const [tab, setTab] = React.useState('dashboard');

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

  return (
    <div style={{
      minHeight: '100vh', background: '#E8E3D6',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px', boxSizing: 'border-box',
    }}>
      <IOSDevice width={390} height={844}>
        <div key={tab} style={{ height: '100%', position: 'relative' }} className="pw-fade-in">
          {renderTab()}
          <TabBar active={tab} onChange={setTab}/>
        </div>
      </IOSDevice>
    </div>
  );
}

Object.assign(window, { MainAppShell });
