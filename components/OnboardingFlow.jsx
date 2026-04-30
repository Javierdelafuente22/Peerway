// Clean onboarding flow — no rails, no tweaks, no debug controls.
// Pure 6-screen flow inside an iOS device frame. Calls onComplete when done.

function OnboardingFlow({ onComplete }) {
  const [step, setStep] = React.useState(0);
  const [state, setState] = React.useState({});

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

  return (
    <div style={{
      minHeight: '100vh', background: '#E8E3D6',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px', boxSizing: 'border-box',
    }}>
      <IOSDevice width={390} height={844}>
        <div key={step} style={{ height: '100%' }}>
          {screens[step]}
        </div>
      </IOSDevice>
    </div>
  );
}

Object.assign(window, { OnboardingFlow });
