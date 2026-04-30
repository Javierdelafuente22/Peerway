// Top-level orchestrator: onboarding -> main app.
//
// Behavior (per user spec):
//   • On a fresh page load (refresh, new tab, "close fake app & open again"),
//     run onboarding from screen 1.
//   • Once onboarding is complete in this session, the user can't go back —
//     they're in the main app until they reload.
//
// We use sessionStorage (cleared when the tab/PWA is closed) AND a fresh-load
// reset, so every refresh starts at onboarding regardless of session state.

function PeerwayRoot() {
  // Always start fresh on every page load. Clearing here means refresh = onboarding.
  const [phase, setPhase] = React.useState(() => {
    // Wipe any stale completion flag on every fresh JS load.
    try { sessionStorage.removeItem('pw_onboarded'); } catch (e) {}
    return 'onboarding';
  });

  const handleOnboardingComplete = () => {
    try { sessionStorage.setItem('pw_onboarded', '1'); } catch (e) {}
    setPhase('app');
  };

  if (phase === 'onboarding') {
    return <OnboardingFlow onComplete={handleOnboardingComplete}/>;
  }
  return <MainAppShell/>;
}

Object.assign(window, { PeerwayRoot });
