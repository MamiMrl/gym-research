/* newsletter-hifi.jsx — hi-fi blocks for "Light Weight" weekly newsletter.
   Black + volt-yellow on off-white. Bebas Neue (display) · Archivo (head/body)
   · JetBrains Mono (labels). Components take (props) incl. accent color + deload. */

const LW = {
  ink:   '#121210',
  paper: '#FAF9F5',
  card:  '#FFFFFF',
  soft:  '#F2F1EA',   // faint section tint
  line:  '#E6E4DB',
  sub:   '#6C6B63',
  faint: '#9C9B91',
  white: '#FFFFFF',
};
const DISPLAY = "'Bebas Neue', 'Arial Narrow', Impact, sans-serif";
const HEAD    = "'Archivo', Helvetica, 'Helvetica Neue', Arial, sans-serif";
const MONO_LW = "'JetBrains Mono', ui-monospace, Menlo, monospace";

// ── shared bits ──────────────────────────────────────────
function Kicker({ children, accent, onDark = false }) {
  return (
    <span style={{ fontFamily: MONO_LW, fontSize: 11, letterSpacing: '0.18em',
      textTransform: 'uppercase', fontWeight: 600, whiteSpace: 'nowrap',
      color: onDark ? '#000' : LW.ink,
      background: accent, padding: '5px 9px', borderRadius: 3, display: 'inline-block' }}>
      {children}
    </span>
  );
}

function SecLabel({ children, accent }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
      <span style={{ width: 9, height: 18, background: accent, display: 'inline-block', borderRadius: 1 }} />
      <span style={{ fontFamily: DISPLAY, fontSize: 26, letterSpacing: '0.04em', color: LW.ink, lineHeight: 1, whiteSpace: 'nowrap' }}>
        {children}
      </span>
    </div>
  );
}

const PAD = 40;

// ── MASTHEAD ─────────────────────────────────────────────
function MastheadLW({ accent, issue = '12', date = 'SUN · JUN 9' }) {
  return (
    <div>
      <div style={{ height: 5, background: accent }} />
      <div style={{ background: LW.ink, padding: `26px ${PAD}px`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 13 }}>
          <div style={{ width: 34, height: 34, background: accent, borderRadius: 6,
            display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontFamily: DISPLAY, fontSize: 24, color: LW.ink, lineHeight: 1, marginTop: 3 }}>L</span>
          </div>
          <span style={{ fontFamily: DISPLAY, fontSize: 34, color: LW.white, letterSpacing: '0.05em', lineHeight: 1 }}>
            LIGHT&nbsp;WEIGHT<span style={{ color: accent }}>.</span>
          </span>
        </div>
        <div style={{ fontFamily: MONO_LW, fontSize: 11, color: 'rgba(255,255,255,.55)',
          textAlign: 'right', lineHeight: 1.6, letterSpacing: '0.04em' }}>
          ISSUE {issue}<br />{date}
        </div>
      </div>
    </div>
  );
}

// ── DELOAD BANNER (conditional) ──────────────────────────
function DeloadBanner({ accent }) {
  return (
    <div style={{ background: accent, padding: `14px ${PAD}px`,
      display: 'flex', alignItems: 'center', gap: 14 }}>
      <span style={{ fontFamily: DISPLAY, fontSize: 24, color: LW.ink, lineHeight: 1, letterSpacing: '0.04em' }}>
        ⚠ DELOAD WEEK
      </span>
      <span style={{ fontFamily: MONO_LW, fontSize: 11, color: 'rgba(0,0,0,.7)', lineHeight: 1.5 }}>
        Same loads · ~50% volume · supercompensate, don't grind.
      </span>
    </div>
  );
}

// ── HERO PHOTO ───────────────────────────────────────────
function HeroPhoto({ accent }) {
  return (
    <div style={{ position: 'relative', lineHeight: 0 }}>
      <image-slot id="lw-hero" shape="rect" placeholder="Drop this week's gym photo · 1200×620"
        style={{ display: 'block', width: '100%', height: '240px' }}></image-slot>
      <div style={{ position: 'absolute', left: PAD, bottom: 18, pointerEvents: 'none' }}>
        <Kicker accent={accent}>Science fact of the week</Kicker>
      </div>
    </div>
  );
}

// ── HERO SCIENCE FACT ────────────────────────────────────
function FactBlock({ accent }) {
  return (
    <div style={{ background: LW.card, padding: `38px ${PAD}px 34px` }}>
      <h1 style={{ margin: 0, fontFamily: HEAD, fontWeight: 800, color: LW.ink,
        fontSize: 33, lineHeight: 1.14, letterSpacing: '-0.02em' }}>
        Hitting a muscle{' '}
        <span style={{ background: accent, padding: '0 6px', boxDecorationBreak: 'clone',
          WebkitBoxDecorationBreak: 'clone' }}>twice a week</span>{' '}
        builds ~15% more of it than once — at the <em style={{ fontStyle: 'italic' }}>same</em> weekly volume.
      </h1>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginTop: 20 }}>
        <span style={{ width: 26, height: 2, background: LW.ink, display: 'inline-block' }} />
        <span style={{ fontFamily: MONO_LW, fontSize: 11.5, color: LW.sub, letterSpacing: '0.02em' }}>
          Schoenfeld, Ogborn &amp; Krieger (2016) · meta-analysis, 25 studies
        </span>
      </div>
      <div style={{ marginTop: 26, borderTop: `1px solid ${LW.line}`, paddingTop: 20 }}>
        <div style={{ fontFamily: MONO_LW, fontSize: 10.5, letterSpacing: '0.16em',
          textTransform: 'uppercase', color: LW.faint, fontWeight: 600, marginBottom: 8 }}>
          Why it matters
        </div>
        <p style={{ margin: 0, fontFamily: HEAD, fontWeight: 600, fontSize: 16.5,
          lineHeight: 1.5, color: LW.ink }}>
          Don't cram chest into one brutal Monday. Split the same sets across two days and
          you grow faster for free — which is exactly how your plan below is built.
        </p>
      </div>
    </div>
  );
}

// ── LAST WEEK RECAP ──────────────────────────────────────
function RecapBlock({ accent, deload }) {
  const tiles = [
    { n: '4/4', l: 'sessions' },
    { n: '+7.5', l: 'kg added', accent: true },
    { n: '0', l: 'skipped' },
  ];
  return (
    <div style={{ background: LW.soft, padding: `32px ${PAD}px`, borderTop: `1px solid ${LW.line}` }}>
      <SecLabel accent={accent}>LAST WEEK</SecLabel>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        {tiles.map((t, i) => (
          <div key={i} style={{ background: LW.card, border: `1px solid ${LW.line}`,
            borderRadius: 10, padding: '18px 10px 14px', textAlign: 'center' }}>
            <div style={{ fontFamily: DISPLAY, fontSize: 42, lineHeight: 0.9,
              color: t.accent ? LW.ink : LW.ink, letterSpacing: '0.01em',
              borderBottom: t.accent ? `3px solid ${accent}` : 'none',
              display: 'inline-block', paddingBottom: t.accent ? 2 : 0 }}>{t.n}</div>
            <div style={{ fontFamily: MONO_LW, fontSize: 10, color: LW.sub, marginTop: 9,
              letterSpacing: '0.1em', textTransform: 'uppercase' }}>{t.l}</div>
          </div>
        ))}
      </div>
      <p style={{ margin: '18px 0 0', fontFamily: HEAD, fontSize: 14.5, lineHeight: 1.5, color: LW.sub }}>
        {deload
          ? 'Six weeks of progression logged — time to back off. This week is built to recover, not grind.'
          : <span>Biggest jump: <strong style={{ color: LW.ink }}>Squat → 90&nbsp;kg</strong>. Momentum's real — keep the form tight.</span>}
      </p>
    </div>
  );
}

// ── THIS WEEK'S PLAN ─────────────────────────────────────
function PlanBlock({ accent, deload }) {
  const days = [
    { d: 'MON', s: 'Upper · Push + Pull',     k: 'Bench Press', w: '70 kg' },
    { d: 'WED', s: 'Lower · All-in',          k: 'Barbell Squat', w: '90 kg' },
    { d: 'FRI', s: 'Cali · Shoulders + Chest',k: 'Machine Press', w: '55 kg' },
    { d: 'SAT', s: 'Deadlift · Back + Quads', k: 'Deadlift', w: '100 kg' },
  ];
  return (
    <div style={{ background: LW.card, padding: `32px ${PAD}px 30px`, borderTop: `1px solid ${LW.line}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
        <SecLabel accent={accent}>THIS WEEK</SecLabel>
        <span style={{ fontFamily: MONO_LW, fontSize: 10, color: LW.sub, letterSpacing: '0.08em',
          whiteSpace: 'nowrap',
          border: `1px solid ${LW.line}`, borderRadius: 20, padding: '5px 11px' }}>
          {deload ? 'DELOAD · 4 DAYS' : 'UPPER/LOWER · 4 DAYS'}
        </span>
      </div>
      <div style={{ border: `1px solid ${LW.line}`, borderRadius: 12, overflow: 'hidden' }}>
        {days.map((x, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14,
            padding: '12px 14px', borderTop: i ? `1px solid ${LW.line}` : 'none' }}>
            <span style={{ fontFamily: DISPLAY, fontSize: 24, color: LW.ink, width: 50,
              flexShrink: 0, letterSpacing: '0.03em', lineHeight: 1 }}>{x.d}</span>
            <span style={{ width: 1, alignSelf: 'stretch', background: LW.line, flexShrink: 0 }} />
            <div style={{ flex: 1, minWidth: 0, paddingLeft: 2 }}>
              <div style={{ fontFamily: HEAD, fontWeight: 700, fontSize: 14.5, color: LW.ink }}>{x.s}</div>
              <div style={{ fontFamily: MONO_LW, fontSize: 11, color: LW.sub, marginTop: 3 }}>
                {x.k} · <span style={{ color: LW.ink, fontWeight: 600 }}>{x.w}</span>
                {deload && <span style={{ color: accent === '#FDE100' ? '#9a8b00' : LW.sub, fontWeight: 600 }}> · ↓ 2 sets</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── DOWNLOAD CTA ─────────────────────────────────────────
function CtaBlock({ accent }) {
  return (
    <div style={{ background: LW.card, padding: `4px ${PAD}px 38px` }}>
      <a href="#" style={{ textDecoration: 'none', display: 'block' }}>
        <div style={{ background: accent, borderRadius: 12, padding: '20px 22px',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 13,
          boxShadow: '0 6px 0 0 rgba(0,0,0,.12)' }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 20, color: LW.ink, lineHeight: 1 }}>↓</span>
          <span style={{ fontFamily: HEAD, fontWeight: 800, fontSize: 17, color: LW.ink, letterSpacing: '0.01em' }}>
            DOWNLOAD THIS WEEK'S PLAN
          </span>
        </div>
      </a>
      <div style={{ textAlign: 'center', marginTop: 13 }}>
        <span style={{ fontFamily: MONO_LW, fontSize: 11, color: LW.faint, letterSpacing: '0.03em' }}>
          PDF · A4 · print &amp; glue into your notebook
        </span>
      </div>
    </div>
  );
}

// ── FOOTER ───────────────────────────────────────────────
function FooterLW({ accent }) {
  return (
    <div style={{ background: LW.ink, padding: `30px ${PAD}px 34px` }}>
      <div style={{ fontFamily: DISPLAY, fontSize: 24, color: LW.white, letterSpacing: '0.05em', lineHeight: 1 }}>
        LIGHT&nbsp;WEIGHT<span style={{ color: accent }}>.</span>
      </div>
      <p style={{ margin: '12px 0 18px', fontFamily: HEAD, fontSize: 13, lineHeight: 1.55, color: 'rgba(255,255,255,.55)', maxWidth: 380 }}>
        Reply with a voice memo telling me how each session went — next Sunday's plan adjusts your loads automatically.
      </p>
      <div style={{ fontFamily: MONO_LW, fontSize: 10.5, color: 'rgba(255,255,255,.4)',
        letterSpacing: '0.08em', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <span>UNSUBSCRIBE</span><span>·</span><span>VIEW ARCHIVE</span><span>·</span><span>SENT EVERY SUNDAY</span>
      </div>
    </div>
  );
}

Object.assign(window, {
  LW, DISPLAY, HEAD, MONO_LW,
  Kicker, SecLabel,
  MastheadLW, DeloadBanner, HeroPhoto, FactBlock, RecapBlock, PlanBlock, CtaBlock, FooterLW,
});
