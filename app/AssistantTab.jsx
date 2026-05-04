// Assistant tab — chat with AI trading agent. Mission-check pattern.
function AssistantTab() {
  const [messages, setMessages] = React.useState([
  {
    role: 'ai',
    type: 'greeting',
    text: "Hi Sarah — I'm your trading agent. I keep an eye on prices and trade your surplus to earn you a bit extra. Tell me about your week and I'll plan around it, or enable smarter intelligence with the top right button.",
    ts: '9:42am'
  }]
  );
  const [input, setInput] = React.useState('');
  const [view, setView] = React.useState('chat'); // 'chat' | 'intelligence'
  const [listening, setListening] = React.useState(false);
  const recognitionRef = React.useRef(null);
  const scrollRef = React.useRef();

  // Web Speech API — speech-to-text. Tap mic, speak, transcript fills the input.
  const speechSupported = typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  const startListening = () => {
    if (!speechSupported) {
      alert("Voice input isn't supported in this browser. Try Safari or Chrome.");
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = 'en-GB';
    rec.interimResults = true;
    rec.continuous = false;

    let finalText = '';
    rec.onresult = (e) => {
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalText += r[0].transcript;
        else interim += r[0].transcript;
      }
      setInput((finalText + interim).trim());
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);

    recognitionRef.current = rec;
    setListening(true);
    rec.start();
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    setListening(false);
  };

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const prompts = [
  "Going on holiday this weekend",
  "Charge my EV by 7am"];


  const runPrompt = (text) => {
    setMessages((m) => [...m, { role: 'user', text, ts: 'now' }]);
    setInput('');

    // Simulate AI response after a beat
    setTimeout(() => {
      const response = aiRespond(text);
      setMessages((m) => [...m, response]);
    }, 700);
  };

  const aiRespond = (text) => {
    const t = text.toLowerCase();

    // 1) HOLIDAY / TRAVEL / AWAY
    if (/\b(holiday|holidays|vacation|away|trip|travel|travelling|traveling|out of town|paris|spain|abroad|weekend away)\b/.test(t)) {
      return {
        role: 'ai', type: 'plan', ts: 'now',
        summary: "Got it — sounds like you'll be away. Here's my plan:",
        plan: [
        { label: 'Sell solar surplus Fri–Sun', detail: 'Est. +£6.80' },
        { label: 'Pause EV charging', detail: 'No sessions scheduled' },
        { label: 'Hold battery at 20%', detail: 'Ready for your return' },
        { label: 'Alert if grid outage', detail: 'Via SMS' }],

        confirm: true
      };
    }

    // 2) WORK SCHEDULE — WFH or office days
    if (/\b(work from home|working from home|wfh|home office|home all day|in the office|at the office|going to work|commute|commuting|workday|work schedule|office today|office tomorrow|in office)\b/.test(t)) {
      const office = /\b(office|going to work|commute|commuting|in office)\b/.test(t);
      if (office) {
        return {
          role: 'ai', type: 'plan', ts: 'now',
          summary: "Okay — out at the office. I'll trade while the house is empty:",
          plan: [
          { label: 'Sell midday solar to peers', detail: 'Est. +£3.40' },
          { label: 'Pause heating, keep fridge', detail: 'Sched. 9am–5pm' },
          { label: 'Pre-warm 30 min before return', detail: 'Comfort on arrival' },
          { label: 'Charge battery from cheap grid', detail: 'For evening peak' }],

          confirm: true
        };
      }
      return {
        role: 'ai', type: 'plan', ts: 'now',
        summary: "Okay — home all day. I'll optimise for your comfort and wallet:",
        plan: [
        { label: 'Power the house from solar', detail: '9am–4pm' },
        { label: 'Sell only true surplus', detail: 'Est. +£1.20' },
        { label: 'Keep battery at 80%+', detail: 'For evening peak' }],

        confirm: true
      };
    }

    // 3) EV CHARGING
    if (/\b(ev|electric vehicle|car|tesla|model [3sxy]|charge|charging|charger|plug in|plug it in)\b/.test(t)) {
      // Try to extract a target time like "by 7am" or "by 8:30"
      const timeMatch = t.match(/by\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?/);
      const targetTime = timeMatch ? timeMatch[0].replace('by ', '') : '7am';
      return {
        role: 'ai', type: 'plan', ts: 'now',
        summary: `EV fully charged by ${targetTime} — here's how:`,
        plan: [
        { label: 'Start charging at 2am', detail: 'Cheapest green window' },
        { label: 'Use battery + cheap grid', detail: 'Est. £2.40 total' },
        { label: 'Target: 80% charge', detail: `Ready ~15 min before ${targetTime}` }],

        confirm: true
      };
    }

    // 4) ENERGY-RELATED but outside the 3 use cases — gentle redirect
    if (/\b(energy|electricity|power|solar|battery|grid|tariff|surplus|kwh|kw|sell|buy|trade|trading|peer|community|bill|saving|savings|price|cheap|peak|off-?peak)\b/.test(t)) {
      return {
        role: 'ai', type: 'message', ts: 'now',
        text: "I can help most with three things right now: holidays/time away, your work schedule, and EV charging. Try one of those and I'll plan around your energy."
      };
    }

    // 5) NON-ENERGY — politely decline
    return {
      role: 'ai', type: 'message', ts: 'now',
      text: "I can only help with energy-related tasks — like managing your solar, planning around holidays or work, or scheduling EV charging. Ask me about any of those!"
    };
  };

  const handleConfirm = (idx, ok) => {
    setMessages((m) => {
      const next = [...m];
      next[idx] = { ...next[idx], confirm: false, resolved: ok ? 'yes' : 'no' };
      if (ok) {
        next.push({
          role: 'ai', type: 'done',
          text: "Done — I'll take care of it. I'll check in if anything changes.",
          ts: 'now'
        });
      } else {
        next.push({
          role: 'ai', type: 'text',
          text: "Okay, holding off. Let me know what you'd like to change.",
          ts: 'now'
        });
      }
      return next;
    });
  };

  if (view === 'intelligence') {
    return <IntelligenceScreen onBack={() => setView('chat')} />;
  }

  return (
    <div className="pw-screen" style={{ display: 'flex', flexDirection: 'column' }}>
      <TabHeader
        eyebrow="Assistant"
        title="Your agent"
        right={
        <button onClick={() => setView('intelligence')} style={{
          appearance: 'none', border: 0, background: 'var(--surface)',
          boxShadow: 'var(--shadow-sm)',
          padding: '8px 12px', borderRadius: 999,
          display: 'flex', alignItems: 'center', gap: 6,
          fontSize: 11, color: 'var(--ink-700)', fontWeight: 600,
          letterSpacing: '0.02em', fontFamily: 'var(--font-mono)',
          cursor: 'pointer'
        }}>
            <IconSparkle size={12} />
            SMARTER
          </button>
        } />
      

      {/* Chat feed */}
      <div ref={scrollRef} className="pw-noscrollbar" style={{
        flex: 1, overflowY: 'auto', padding: '0 16px 12px',
        display: 'flex', flexDirection: 'column', gap: 10
      }}>
        {messages.map((m, i) =>
        <ChatBubble key={i} msg={m} idx={i} onConfirm={handleConfirm} />
        )}
      </div>

      {/* Prompt chips — just 2, no scroll */}
      <div style={{
        padding: '8px 16px 0',
        display: 'flex', gap: 8, flexWrap: 'wrap'
      }}>
        {prompts.map((p) =>
        <button key={p} onClick={() => runPrompt(p)} style={{
          appearance: 'none', border: '1px solid var(--cream-200)',
          background: 'var(--surface)',
          padding: '8px 12px', borderRadius: 999,
          fontSize: 12, color: 'var(--ink-700)', fontWeight: 500,
          cursor: 'pointer', flexShrink: 0,
          letterSpacing: '-0.005em'
        }}>
            {p}
          </button>
        )}
      </div>

      {/* Input dock */}
      <div style={{
        padding: '12px 16px 84px',
        background: 'linear-gradient(180deg, transparent, var(--cream-50) 40%)'
      }}>
        <form onSubmit={(e) => {e.preventDefault();if (input.trim()) runPrompt(input.trim());}}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: 6, background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 999,
          boxShadow: 'var(--shadow-sm)'
        }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={listening ? "Listening…" : "Ask or tell me anything…"}
            style={{
              flex: 1, border: 0, background: 'transparent', outline: 'none',
              padding: '8px 10px', fontSize: 14,
              color: 'var(--ink-900)', fontFamily: 'var(--font-sans)'
            }} />
          
          {input.trim() ?
          <button type="submit" style={{
            appearance: 'none', border: 0, cursor: 'pointer',
            width: 38, height: 38, borderRadius: 999,
            background: 'var(--ink-900)', color: 'var(--lime-400)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
              <IconSend size={16} />
            </button> :

          <button type="button"
            onClick={() => listening ? stopListening() : startListening()}
            aria-label={listening ? 'Stop listening' : 'Start voice input'}
            style={{
              appearance: 'none', border: 0, cursor: 'pointer',
              width: 38, height: 38, borderRadius: 999,
              background: listening ? 'var(--ink-900)' : 'var(--lime-500)',
              color: listening ? 'var(--lime-400)' : 'var(--ink-900)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: listening
                ? '0 0 0 4px rgba(0,168,98,0.25)'
                : '0 2px 8px rgba(0,168,98,0.3)',
              transition: 'all .18s ease',
              animation: listening ? 'pwMicPulse 1.2s ease-in-out infinite' : 'none'
            }}>
              <IconMic size={18} />
            </button>
          }
          <style>{`
            @keyframes pwMicPulse {
              0%, 100% { box-shadow: 0 0 0 0 rgba(0,168,98,0.45); }
              50%      { box-shadow: 0 0 0 8px rgba(0,168,98,0.0); }
            }
          `}</style>
        </form>
      </div>
    </div>);

}

function ChatBubble({ msg, idx, onConfirm }) {
  if (msg.role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', paddingLeft: 40 }}>
        <div style={{
          background: 'var(--ink-900)', color: '#fff',
          padding: '10px 14px', borderRadius: '18px 18px 4px 18px',
          fontSize: 14, lineHeight: 1.4,
          maxWidth: '85%', letterSpacing: '-0.005em'
        }}>
          {msg.text}
        </div>
      </div>);

  }

  // AI
  return (
    <div style={{ display: 'flex', gap: 8, paddingRight: 40 }}>
      <div style={{
        width: 28, height: 28, borderRadius: 999,
        background: 'var(--lime-500)', color: 'var(--ink-900)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0, marginTop: 2
      }}>
        <IconSparkle size={12} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {msg.type === 'plan' ?
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: '4px 18px 18px 18px',
          padding: '12px 14px'
        }}>
            <div style={{
            fontSize: 14, color: 'var(--ink-900)', lineHeight: 1.4,
            marginBottom: 10, fontWeight: 500,
            letterSpacing: '-0.005em', textWrap: 'pretty'
          }}>
              {msg.summary}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
              {msg.plan.map((step, i) =>
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: 8,
              padding: '8px 10px',
              background: 'var(--cream-50)',
              borderRadius: 8
            }}>
                  <div style={{
                width: 18, height: 18, borderRadius: 999,
                background: 'var(--ink-900)', color: '#fff',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 600,
                flexShrink: 0, fontFamily: 'var(--font-mono)'
              }}>
                    {i + 1}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: 'var(--ink-900)', fontWeight: 500, letterSpacing: '-0.005em' }}>
                      {step.label}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--ink-600)', marginTop: 1 }}>
                      {step.detail}
                    </div>
                  </div>
                </div>
            )}
            </div>
            {msg.confirm ?
          <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => onConfirm(idx, true)} style={{
              flex: 1, appearance: 'none', border: 0, cursor: 'pointer',
              height: 38, borderRadius: 10,
              background: 'var(--ink-900)', color: '#fff',
              fontSize: 13, fontWeight: 600,
              fontFamily: 'var(--font-sans)',
              letterSpacing: '-0.005em'
            }}>
                  Yes, do it
                </button>
                <button onClick={() => onConfirm(idx, false)} style={{
              flex: 1, appearance: 'none',
              border: '1px solid var(--cream-200)',
              background: 'var(--surface)',
              cursor: 'pointer', height: 38, borderRadius: 10,
              color: 'var(--ink-700)',
              fontSize: 13, fontWeight: 500,
              fontFamily: 'var(--font-sans)',
              letterSpacing: '-0.005em'
            }}>
                  Not yet
                </button>
              </div> :
          msg.resolved === 'yes' ?
          <div style={{
            padding: '6px 10px', borderRadius: 8,
            background: 'var(--lime-50)', color: 'var(--lime-600)',
            fontSize: 11, fontWeight: 600, letterSpacing: '0.02em',
            fontFamily: 'var(--font-mono)', textTransform: 'uppercase',
            display: 'inline-flex', alignItems: 'center', gap: 6
          }}>
                <IconCheck size={12} /> CONFIRMED
              </div> :
          null}
          </div> :

        <div style={{
          background: msg.type === 'done' ? 'var(--lime-50)' : 'var(--surface)',
          border: '1px solid ' + (msg.type === 'done' ? 'var(--lime-100)' : 'var(--cream-200)'),
          borderRadius: '4px 18px 18px 18px',
          padding: '10px 14px',
          fontSize: 14, color: 'var(--ink-900)', lineHeight: 1.4,
          letterSpacing: '-0.005em', textWrap: 'pretty'
        }}>
            {msg.text}
          </div>
        }
        <div style={{
          fontSize: 10, color: 'var(--ink-400)', marginTop: 4,
          fontFamily: 'var(--font-mono)', letterSpacing: '0.02em'
        }}>
          {msg.ts}
        </div>
      </div>
    </div>);

}

// Dedicated explainer screen — NOT a modal.
function IntelligenceScreen({ onBack }) {
  const [cal, setCal] = React.useState(false);
  const [email, setEmail] = React.useState(false);
  const anyOn = cal || email;

  return (
    <div className="pw-screen">
      <div style={{
        padding: '58px 24px 16px',
        background: 'var(--cream-50)',
        position: 'sticky', top: 0, zIndex: 2
      }}>
        <button onClick={onBack} style={{
          appearance: 'none', border: 0, background: 'transparent',
          padding: 0, color: 'var(--ink-600)',
          display: 'flex', alignItems: 'center', gap: 4,
          fontSize: 13, cursor: 'pointer', marginBottom: 14
        }}>
          <IconChevron size={14} dir="left" />
          <span>Back to assistant</span>
        </button>

        <div className="t-label" style={{ color: 'var(--lime-500)', marginBottom: 6 }}>
          Smarter intelligence
        </div>
        <h1 className="t-title" style={{
          fontSize: 28, lineHeight: 1.08, margin: 0,
          color: 'var(--ink-900)', fontWeight: 600, letterSpacing: '-0.025em'
        }}>
          Optimise your energy.
        </h1>
      </div>

      <div style={{ padding: '12px 24px 120px' }}>
        <p style={{
          fontSize: 14, color: 'var(--ink-700)', lineHeight: 1.55,
          marginBottom: 22, textWrap: 'pretty'
        }}>Connect to your apps so I can plan ahead — selling more energy when you're away and charging your EV before you need it.

        </p>

        {/* Granular toggles */}
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--cream-200)',
          borderRadius: 'var(--r-md)',
          marginBottom: 20, overflow: 'hidden'
        }}>
          <IntelToggle
            title="Calendar"
            detail="I'll only scan for meeting events. I'll never read your meeting notes."
            on={cal} onChange={setCal} />
          
          <div style={{ borderTop: '1px solid var(--cream-200)' }} />
          <IntelToggle
            title="Email"
            detail="I'll only scan for travel confirmations to manage your home while you're away."
            on={email} onChange={setEmail} />
          
        </div>

        {/* What we won't do */}
        <div style={{
          background: 'var(--ink-900)', color: '#fff',
          borderRadius: 'var(--r-md)',
          padding: 18, marginBottom: 20
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: 999,
              background: 'rgba(0,192,111,0.20)', color: 'var(--lime-400)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <IconShield size={14} />
            </div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>What we won't do</div>
          </div>
          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
            'Read personal messages',
            'Store anything beyond travel events',
            'Share your schedule with other users',
            'Sell or share your data with advertisers'].
            map((t) =>
            <li key={t} style={{
              display: 'flex', alignItems: 'flex-start', gap: 10,
              fontSize: 13, color: 'rgba(255,255,255,0.85)', lineHeight: 1.45
            }}>
                <span style={{
                width: 16, height: 16, borderRadius: 999,
                background: 'rgba(255,255,255,0.08)',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, marginTop: 1, color: 'rgba(255,255,255,0.5)'
              }}>
                  <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor"><path d="M1 1l6 6M7 1l-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
                </span>
                {t}
              </li>
            )}
          </ul>
        </div>

        <button disabled={!anyOn} className="pw-btn pw-btn-primary" style={{
          width: '100%', height: 52,
          opacity: anyOn ? 1 : 0.4,
          cursor: anyOn ? 'pointer' : 'not-allowed'
        }}>Enable smarter intelligence

        </button>
        <div style={{
          fontSize: 11, color: 'var(--ink-400)', textAlign: 'center',
          marginTop: 10, letterSpacing: '-0.005em'
        }}>
          Revocable anytime from Profile → Data
        </div>
      </div>
    </div>);

}

function IntelToggle({ title, detail, on, onChange }) {
  return (
    <button onClick={() => onChange(!on)} style={{
      appearance: 'none', border: 0, background: 'transparent',
      width: '100%', padding: '14px 16px', cursor: 'pointer',
      display: 'flex', alignItems: 'center', gap: 12, textAlign: 'left'
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, color: 'var(--ink-900)', fontWeight: 600, letterSpacing: '-0.005em' }}>
          {title}
        </div>
        <div style={{ fontSize: 12, color: 'var(--ink-600)', marginTop: 2, lineHeight: 1.4 }}>
          {detail}
        </div>
      </div>
      <div style={{
        width: 42, height: 24, borderRadius: 999,
        background: on ? 'var(--lime-500)' : 'var(--cream-200)',
        position: 'relative', flexShrink: 0,
        transition: 'background .18s'
      }}>
        <div style={{
          position: 'absolute', top: 2, left: on ? 20 : 2,
          width: 20, height: 20, borderRadius: 999,
          background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
          transition: 'left .18s'
        }} />
      </div>
    </button>);

}

Object.assign(window, { AssistantTab });