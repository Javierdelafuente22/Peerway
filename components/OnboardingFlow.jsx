// Clean onboarding flow — 6-screen flow. Calls onComplete when done.
// In PWA/standalone mode, renders full-screen with no frame.
// In a browser window (desktop preview), keeps the centered IOSDevice card.

function OnboardingFlow({ onComplete }) {
  const [step, setStep] = React.useState(0);
  const [state, setState] = React.useState({});

  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  const goNext = () => {
    if (step >= 5) {
      onComplete && onComplete();
    } else {
      setStep(s => s + 1);
    }
  };
  const goBack = () => setStep(s => Math.max(0, s - 1));

  const screens = [
    <Screen1_Postcode key="s1" state={state} setState={setState} onNext={goNext}/>,
    <Screen2_Connected key="s2" provider="your energy provider" onNext={goNext}/>,
    <Screen3_Savings   key="s3" state={state} onNext={goNext} onBack={goBack}/>,
    <Screen4_Profile   key="s4" state={state} setState={setState} onNext={goNext} onBack={goBack}/>,
    <Screen5_Legal     key="s5" onNext={goNext} onBack={goBack}/>,
    <Screen6_AllSet    key="s6" onNext={goNext} onBack={goBack}/>,
  ];

  const content = (
    <div key={step} style={{ height: '100%' }}>
      {screens[step]}
    </div>
  );

  // PWA / standalone → full-screen, no frame
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

Object.assign(window, { OnboardingFlow });
