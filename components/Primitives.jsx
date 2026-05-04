// Shared primitives for Peerway onboarding.

// Primary forest-green button with optional arrow.
function PwButton({ children, onClick, disabled, variant = 'primary', icon, style, ...rest }) {
  const klass = variant === 'ghost' ? 'pw-btn pw-btn--ghost' : 'pw-btn';
  return (
    <button className={klass} onClick={onClick} disabled={disabled} style={style} {...rest}>
      <span>{children}</span>
      {icon}
    </button>
  );
}

// Logo mark — a stylized "P" made of two energy waves.
function PeerwayMark({ size = 32, color = 'var(--forest-700)' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" style={{ display: 'block' }}>
      <defs>
        <clipPath id="pwClip"><rect width="32" height="32" rx="9"/></clipPath>
      </defs>
      <g clipPath="url(#pwClip)">
        <rect width="32" height="32" fill={color}/>
        <path d="M-2 22c4-3 6-3 10 0s6 3 10 0 6-3 10 0 6 3 10 0"
              stroke="rgba(255,255,255,0.35)" strokeWidth="1.2" fill="none"/>
        <path d="M-2 18c4-3 6-3 10 0s6 3 10 0 6-3 10 0 6 3 10 0"
              stroke="rgba(255,255,255,0.55)" strokeWidth="1.4" fill="none"/>
        <path d="M9.5 8h7.5a5 5 0 010 10H13v6h-3.5V8z"
              fill="#fff" fillOpacity="0.96"/>
        <circle cx="17" cy="13" r="2" fill={color}/>
      </g>
    </svg>
  );
}

// Peerway wordmark (logo + name)
function PeerwayLogo({ size = 22 }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      <PeerwayMark size={size + 4}/>
      <span className="t-display" style={{
        fontSize: size, lineHeight: 1, color: 'var(--ink-900)', letterSpacing: '-0.01em',
        fontWeight: 400,
      }}>Peerway</span>
    </div>
  );
}

// Progress dots for the onboarding flow
function PwProgress({ current, total = 6 }) {
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
      {Array.from({ length: total }).map((_, i) => {
        const active = i === current;
        const past = i < current;
        return (
          <div key={i} style={{
            width: active ? 22 : 6,
            height: 6,
            borderRadius: 3,
            background: active ? 'var(--forest-700)' : (past ? 'var(--forest-300)' : 'var(--cream-200)'),
            transition: 'all .32s cubic-bezier(.22,.8,.32,1)',
          }}/>
        );
      })}
    </div>
  );
}

// Screen frame — sets padding + houses progress header
function PwScreen({ children, onBack, step, totalSteps = 6, style }) {
  return (
    <div className="pw-screen pw-fade-in" style={style}>
      <div style={{
        position: 'sticky', top: 0, zIndex: 2,
        background: 'var(--cream-50)',
        padding: '58px 24px 12px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <button onClick={onBack} style={{
          appearance: 'none', border: 0, background: 'transparent',
          width: 36, height: 36, borderRadius: 999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--ink-600)', cursor: onBack ? 'pointer' : 'default',
          opacity: onBack ? 1 : 0,
        }}>
          <IconChevron dir="left" size={18}/>
        </button>
        {typeof step === 'number' && <PwProgress current={step} total={totalSteps}/>}
        <div style={{ width: 36 }}/>
      </div>
      <div style={{ padding: '8px 24px 32px' }}>
        {children}
      </div>
    </div>
  );
}

// Consistent page title used by every screen for hierarchy.
// Renders as: [eyebrow uppercase] TITLE (32-36px) [subtitle 15px muted]
function PwPageTitle({ eyebrow, title, subtitle, size = 32 }) {
  return (
    <div style={{ marginTop: 12, marginBottom: 24 }}>
      {eyebrow && (
        <div className="t-label" style={{ fontSize: 13, color: 'var(--lime-600)', marginBottom: 10 }}>
          {eyebrow}
        </div>
      )}
      <h1 className="t-title" style={{
        fontSize: size, lineHeight: 1.04, margin: '0 0 10px',
        color: 'var(--ink-900)', fontWeight: 600, letterSpacing: '-0.03em',
      }}>
        {title}
      </h1>
      {subtitle && (
        <p className="t-body" style={{
          fontSize: 15, lineHeight: 1.45, color: 'var(--ink-600)', margin: 0,
          maxWidth: 360,
        }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}

// Small info tooltip — auto-positions left vs right based on x
function PwTooltip({ label }) {
  const [open, setOpen] = React.useState(false);
  const [side, setSide] = React.useState('right'); // tooltip sits on which side of trigger
  const btnRef = React.useRef(null);
  React.useEffect(() => {
    if (open && btnRef.current) {
      const r = btnRef.current.getBoundingClientRect();
      // Find the nearest phone screen container width
      const host = btnRef.current.closest('.pw-screen');
      const hostRight = host ? host.getBoundingClientRect().right : window.innerWidth;
      const hostLeft  = host ? host.getBoundingClientRect().left : 0;
      const rightSpace = hostRight - r.right;
      const leftSpace  = r.left - hostLeft;
      setSide(rightSpace < 140 && leftSpace > rightSpace ? 'left' : 'right');
    }
  }, [open]);

  return (
    <div style={{ position: 'relative', display: 'inline-flex' }}>
      <button ref={btnRef} onClick={() => setOpen(o => !o)} style={{
        appearance: 'none', background: 'transparent', border: 0, padding: 0,
        color: 'var(--ink-400)', cursor: 'pointer',
        display: 'inline-flex', alignItems: 'center',
      }} aria-label="Why we need this">
        <IconInfo size={14}/>
      </button>
      {open && (
        <div role="tooltip" onClick={() => setOpen(false)} style={{
          position: 'absolute', top: '140%',
          ...(side === 'right' ? { left: -8 } : { right: -8 }),
          zIndex: 10,
          width: 220, padding: '10px 12px',
          background: 'var(--ink-900)', color: '#F2EFE7',
          borderRadius: 10, fontSize: 12, lineHeight: 1.45,
          boxShadow: 'var(--shadow-lg)',
          letterSpacing: '-0.005em',
        }}>
          <div style={{
            position: 'absolute', top: -5,
            ...(side === 'right' ? { left: 12 } : { right: 12 }),
            width: 10, height: 10,
            background: 'var(--ink-900)', transform: 'rotate(45deg)',
          }}/>
          {label}
        </div>
      )}
    </div>
  );
}

// Reassurance box (used on screen 5)
function PwReassurance({ title, children }) {
  return (
    <div style={{
      background: 'var(--forest-900)', color: '#F2EFE7',
      padding: '16px 18px', borderRadius: 'var(--r-lg)',
      display: 'flex', gap: 12, alignItems: 'flex-start',
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: 999, flexShrink: 0,
        background: 'rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#CFE1D5',
      }}>
        <IconShield size={16}/>
      </div>
      <div>
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 2, color: '#fff' }}>{title}</div>
        <div style={{ fontSize: 13, lineHeight: 1.5, color: 'rgba(242,239,231,0.75)' }}>
          {children}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  PwButton, PeerwayMark, PeerwayLogo, PwProgress, PwScreen, PwTooltip, PwReassurance,
  PwPageTitle,
});
