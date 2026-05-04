// Screen 5 — Legal + consent with expandable detail panels
function Screen5_Legal({ onNext, onBack }) {
  const [agreed, setAgreed] = React.useState(false);
  const [openItem, setOpenItem] = React.useState(null);

  const items = [
    {
      label: 'Terms of Service',
      desc: 'How Peerway operates and what you agree to.',
      icon: <IconDoc size={14}/>,
      content: (
        <div>
          <p style={{ marginTop: 0 }}>
            <strong>What Peerway does.</strong> Peerway is a platform that matches households who generate surplus solar electricity with nearby neighbours who want to buy it at a cheaper rate than the grid. We act as a technology intermediary — we are not your energy supplier and do not replace them.
          </p>
          <p>
            <strong>Your supplier stays the same.</strong> All energy continues to flow through the national grid and is settled through your existing supplier (e.g. Octopus Energy). Peerway coordinates the commercial matching and billing adjustments — your lights stay on regardless.
          </p>
          <p>
            <strong>Automated trading.</strong> Once you opt in, Peerway automatically matches your surplus generation or consumption with peers in your local area. You can pause or stop trading at any time from your profile settings. No lock-in, no exit fees, no minimum term.
          </p>
          <p>
            <strong>Pricing.</strong> Peer trades are settled at rates between the grid export rate and the standard import rate — meaning sellers earn more and buyers pay less than they would on a standard tariff. Peerway takes a small platform fee (shown transparently in your dashboard). Rates may vary with market conditions.
          </p>
          <p>
            <strong>Regulatory basis.</strong> Peerway operates under Ofgem's regulatory framework for peer-to-peer energy trading. Smart meter data is accessed via your supplier's authorised API under the Smart Energy Code (SEC). We comply with all applicable provisions of the Electricity Act 1989 and the Energy Act 2023.
          </p>
          <p>
            <strong>Liability.</strong> Peerway is not liable for interruptions to your energy supply, which remains the responsibility of your licensed supplier and your distribution network operator (DNO). We are liable for the accuracy of trade matching and billing within the platform.
          </p>
          <p style={{ marginBottom: 0 }}>
            <strong>Changes to these terms.</strong> We will notify you by email and in-app at least 30 days before any material change to these terms takes effect. You can reject changes by closing your account at any time.
          </p>
        </div>
      ),
    },
    {
      label: 'Your data',
      desc: "What we collect, why, and where it's stored (UK only).",
      icon: <IconShield size={14}/>,
      content: (
        <div>
          <p style={{ marginTop: 0 }}>
            <strong>What we collect.</strong> Your name, email, postcode, smart meter MPAN, half-hourly consumption and generation readings, and basic household profile (e.g. whether you have solar panels or an EV). We do not collect financial details — billing is handled by your energy supplier.
          </p>
          <p>
            <strong>Why we collect it.</strong> To match you with trading peers, calculate your savings, and settle trades accurately. Each piece of data has a specific, stated purpose — we do not collect anything speculatively.
          </p>
          <p>
            <strong>Lawful basis.</strong> We process your data under Article 6(1)(b) of the UK GDPR (performance of a contract) for core trading functions, and Article 6(1)(a) (consent) for optional features like community benchmarking. You can withdraw consent for optional features at any time without affecting the core service.
          </p>
          <p>
            <strong>Where it is stored.</strong> All personal data is stored on servers located in the United Kingdom. We do not transfer your data outside the UK. If this ever changes, we will obtain your explicit consent first and ensure adequate protections are in place as required by the UK GDPR (Chapter V).
          </p>
          <p>
            <strong>Who has access.</strong> Only Peerway staff who need your data to operate the service can access it. We do not sell, rent, or share your personal data with third parties for marketing purposes. Your energy supplier receives only the trade settlement data necessary to adjust your bill.
          </p>
          <p>
            <strong>How long we keep it.</strong> We retain your trading data for 6 years after your last transaction (aligned with HMRC record-keeping requirements). If you delete your account, personal identifiers are removed within 30 days; anonymised trading records are kept for regulatory compliance.
          </p>
          <p style={{ marginBottom: 0 }}>
            <strong>Your rights under the UK GDPR.</strong> You have the right to access, rectify, restrict processing of, and port your personal data. You also have the right to object to processing and to lodge a complaint with the Information Commissioner's Office (ICO) at <span style={{ fontWeight: 500 }}>ico.org.uk</span>. See the section below on erasure for deletion rights.
          </p>
        </div>
      ),
    },
    {
      label: 'Right to erasure',
      desc: 'Delete everything at any time, no questions asked.',
      icon: <IconTrash size={14}/>,
      content: (
        <div>
          <p style={{ marginTop: 0 }}>
            <strong>Your right.</strong> Under Article 17 of the UK GDPR, you have the right to request the deletion of all personal data we hold about you. We honour this without requiring a reason.
          </p>
          <p>
            <strong>How to request it.</strong> Go to Profile → Your Data (GDPR) → Delete my account, or email <span style={{ fontWeight: 500 }}>privacy@peerway.co.uk</span>. We will confirm receipt within 48 hours and complete the deletion within 30 calendar days, as required by UK GDPR Article 12(3).
          </p>
          <p>
            <strong>What gets deleted.</strong> Your name, email, postcode, meter details, household profile, and all personally identifiable trading history. Your account and all associated data are permanently and irreversibly removed from our systems and any backups within the 30-day window.
          </p>
          <p>
            <strong>What we may retain.</strong> We are legally required to keep certain anonymised, non-identifiable records for regulatory and tax compliance (e.g. aggregated settlement data required by Ofgem and HMRC). These records cannot be linked back to you in any way.
          </p>
          <p style={{ marginBottom: 0 }}>
            <strong>Data portability.</strong> Before deleting your account, you can export your full trading history, consumption data, and savings records in a standard machine-readable format (CSV) from Profile → Your Data → Export. This is your right under Article 20 of the UK GDPR.
          </p>
        </div>
      ),
    },
  ];

  // If a detail panel is open, show it full-screen
  if (openItem !== null) {
    const item = items[openItem];
    return (
      <PwScreen>
        <div style={{
          position: 'sticky', top: 0, zIndex: 3,
          background: 'var(--cream-50)',
          padding: '0 0 12px',
        }}>
          <button onClick={() => setOpenItem(null)} style={{
            appearance: 'none', border: 0, background: 'transparent',
            display: 'flex', alignItems: 'center', gap: 6,
            color: 'var(--ink-700)', fontSize: 15, fontWeight: 500,
            fontFamily: 'var(--font-sans)', cursor: 'pointer',
            padding: '4px 0',
          }}>
            <IconChevron dir="left" size={16}/>
            <span>Back to consent</span>
          </button>
        </div>

        <div style={{ marginTop: 8 }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'var(--lime-50)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--ink-900)',
            }}>{item.icon}</div>
            <h2 className="t-title" style={{
              fontSize: 22, margin: 0, color: 'var(--ink-900)',
              fontWeight: 600, letterSpacing: '-0.02em',
            }}>{item.label}</h2>
          </div>

          <div style={{
            fontSize: 14, lineHeight: 1.65, color: 'var(--ink-700)',
            fontFamily: 'var(--font-sans)',
          }}>
            {item.content}
          </div>
        </div>
      </PwScreen>
    );
  }

  return (
    <PwScreen step={4} onBack={onBack}>
      <PwPageTitle
        eyebrow="Step 4 — Consent"
        title="Terms, in plain English."
        subtitle="The short version of how your data is handled is below."
        size={32}
      />

      {/* Reassurance */}
      <div style={{ marginTop: 4 }}>
        <PwReassurance title="Why Peerway saves you money.">
          Trading with peers means you buy for less and sell for more versus a standard grid tariff.
        </PwReassurance>
      </div>

      {/* List of legal items */}
      <div className="pw-card" style={{ marginTop: 20, overflow: 'hidden' }}>
        {items.map((it, i) => (
          <button key={i} onClick={() => setOpenItem(i)} style={{
            appearance: 'none', border: 0, background: 'transparent',
            width: '100%', textAlign: 'left', cursor: 'pointer',
            padding: '14px 18px',
            display: 'flex', alignItems: 'flex-start', gap: 12,
            borderTop: i === 0 ? 0 : '1px solid var(--cream-200)',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: 'var(--lime-50)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--ink-900)', flexShrink: 0, marginTop: 2,
            }}>{it.icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 15, color: 'var(--ink-900)', fontWeight: 500 }}>
                {it.label}
              </div>
              <div style={{ fontSize: 13, color: 'var(--ink-600)', marginTop: 2, lineHeight: 1.4 }}>
                {it.desc}
              </div>
            </div>
            <div style={{ color: 'var(--ink-400)', marginTop: 4, flexShrink: 0 }}>
              <IconChevron size={14}/>
            </div>
          </button>
        ))}
      </div>

      {/* Consent checkbox */}
      <button
        type="button"
        onClick={() => setAgreed(a => !a)}
        style={{
          appearance: 'none', width: '100%', textAlign: 'left', cursor: 'pointer',
          marginTop: 20, display: 'flex', gap: 12, alignItems: 'flex-start',
          padding: '14px 16px',
          background: agreed ? 'var(--lime-50)' : 'var(--surface)',
          border: `1px solid ${agreed ? 'var(--lime-500)' : 'var(--cream-200)'}`,
          borderRadius: 'var(--r-md)',
          transition: 'background .18s, border-color .18s',
          fontFamily: 'var(--font-sans)',
        }}>
        <div style={{
          width: 22, height: 22, borderRadius: 6,
          border: `1.5px solid ${agreed ? 'var(--ink-900)' : 'var(--ink-300)'}`,
          background: agreed ? 'var(--ink-900)' : 'transparent',
          flexShrink: 0, marginTop: 1,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all .16s',
        }}>
          {agreed && <span style={{ color: 'var(--lime-400)', display: 'flex' }}><IconCheck size={14}/></span>}
        </div>
        <span style={{ fontSize: 14, lineHeight: 1.5, color: 'var(--ink-700)' }}>
          I agree to Peerway's Terms and Privacy policy, and consent to automated trading.
        </span>
      </button>

      <div style={{ marginTop: 20 }}>
        <PwButton onClick={onNext} disabled={!agreed} icon={<IconArrowRight size={16}/>}>
          Accept & continue
        </PwButton>
      </div>
    </PwScreen>
  );
}

Object.assign(window, { Screen5_Legal });
