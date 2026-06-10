/* newsletter-elevated.jsx — "performance-lab" elevation of the weekly newsletter.
   System: Big Shoulders Stencil (display) · Archivo (body) · JetBrains Mono (spec).
   Volt is RATIONED: hairline rules, one underline, one CTA block. No rounded
   cards, no shadows — hairlines + whitespace carry the craft. */

const EL = {
  ink:    '#15140F',
  paper:  '#FBFAF5',
  bone:   '#F4F2EA',
  line:   '#E4E1D5',
  hair:   '#D9D6C8',
  sub:    '#6E6C60',
  faint:  '#9A9789',
  white:  '#F5F3EC',
  voltText: '#857A00', // legible derivative for small accent text on light
};
const EL_DISPLAY = "'Big Shoulders Stencil', 'Big Shoulders Stencil Display', 'Arial Narrow', Impact, sans-serif";
const EL_HEAD    = "'Archivo', Helvetica, 'Helvetica Neue', Arial, sans-serif";
const EL_MONO    = "'JetBrains Mono', ui-monospace, Menlo, monospace";
const EPAD = 44;

// ── shared spec bits ─────────────────────────────────────
function SpecLabel({ children, color = EL.faint, wrap = false }) {
  return (
    <span style={{ fontFamily: EL_MONO, fontSize: 10, letterSpacing: '0.22em',
      textTransform: 'uppercase', fontWeight: 600, color,
      whiteSpace: wrap ? 'normal' : 'nowrap' }}>
      {children}
    </span>
  );
}

function SectionHead({ index, title, right }) {
  return (
    <div style={{ borderTop: `1px solid ${EL.ink}`, paddingTop: 12, marginBottom: 22,
      display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
        <SpecLabel color={EL.ink}>{index}</SpecLabel>
        <SpecLabel color={EL.ink}>{title}</SpecLabel>
      </div>
      {right ? <SpecLabel>{right}</SpecLabel> : null}
    </div>
  );
}

// ── MASTHEAD ─────────────────────────────────────────────
function MastheadEL({ accent, name = 'LIGHT WEIGHT', issue = '012', date = 'SUN — JUN 14, 2026' }) {
  return (
    <div style={{ background: EL.ink }}>
      <div style={{ height: 3, background: accent }} />
      <div style={{ padding: `16px ${EPAD}px 0`, display: 'flex',
        justifyContent: 'space-between', alignItems: 'center' }}>
        <SpecLabel color="rgba(245,243,236,.5)">Weekly Training Brief</SpecLabel>
        <SpecLabel color="rgba(245,243,236,.5)">No. {issue}</SpecLabel>
      </div>
      <div style={{ padding: `18px ${EPAD}px 0`, textAlign: 'center' }}>
        <div style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 76,
          lineHeight: 0.92, color: EL.white, letterSpacing: '0.015em', whiteSpace: 'nowrap' }}>
          {name}<span style={{ color: accent }}>.</span>
        </div>
      </div>
      <div style={{ margin: `20px ${EPAD}px 0`, borderTop: '1px solid rgba(245,243,236,.18)',
        padding: '12px 0 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <SpecLabel color="rgba(245,243,236,.5)">{date}</SpecLabel>
        <SpecLabel color="rgba(245,243,236,.5)">Upper / Lower · 4 Days</SpecLabel>
      </div>
    </div>
  );
}

// ── DELOAD STRIP (conditional) ───────────────────────────
function DeloadStrip({ accent }) {
  return (
    <div style={{ background: EL.ink, borderTop: `1px solid rgba(245,243,236,.18)`,
      padding: `13px ${EPAD}px`, display: 'flex', alignItems: 'center', gap: 14 }}>
      <span style={{ width: 8, height: 8, background: accent, flexShrink: 0 }} />
      <SpecLabel color={EL.white}>Deload — Week 7 of 7</SpecLabel>
      <span style={{ fontFamily: EL_HEAD, fontSize: 12, color: 'rgba(245,243,236,.6)', lineHeight: 1.4 }}>
        Same loads, half the volume. Growth happens this week — let it.
      </span>
    </div>
  );
}

// ── HERO — full bleed, type over image ───────────────────
function HeroEL({ accent, deload }) {
  return (
    <div style={{ position: 'relative', lineHeight: 0, background: EL.ink }}>
      <div style={{ filter: 'grayscale(1) contrast(1.08) brightness(.96)', background: '#E9E6DB' }}>
        <image-slot id="lw2-hero" shape="rect" placeholder="Drop hero photo · 1200×680 · it will render B&W"
          style={{ display: 'block', width: '100%', height: '340px' }}></image-slot>
      </div>
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
        background: 'linear-gradient(to top, rgba(21,20,15,.88) 0%, rgba(21,20,15,.25) 48%, rgba(21,20,15,0) 75%)' }} />
      <div style={{ position: 'absolute', left: EPAD, right: EPAD, bottom: 26, pointerEvents: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <span style={{ width: 22, height: 3, background: accent, display: 'inline-block' }} />
          <SpecLabel color={EL.white}>Field Note 012 — Frequency</SpecLabel>
        </div>
        <div style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 62, lineHeight: 0.94,
          color: EL.white, letterSpacing: '0.015em' }}>
          {deload ? 'BACK OFF TO GROW.' : 'TRAIN IT TWICE.'}
        </div>
      </div>
    </div>
  );
}

// ── 01 / THE SCIENCE ─────────────────────────────────────
function ScienceEL({ accent }) {
  return (
    <div style={{ background: EL.paper, padding: `34px ${EPAD}px 36px` }}>
      <SectionHead index="01" title="The Science" right="Meta-analysis · n=25" />
      <h1 style={{ margin: 0, fontFamily: EL_HEAD, fontWeight: 700, color: EL.ink,
        fontSize: 27, lineHeight: 1.24, letterSpacing: '-0.015em' }}>
        Hitting a muscle{' '}
        <span style={{ borderBottom: `4px solid ${accent}`, paddingBottom: 1 }}>twice a week</span>{' '}
        builds ~15% more of it than once — at the same weekly volume.
      </h1>
      <div style={{ marginTop: 18 }}>
        <SpecLabel>Schoenfeld · Ogborn · Krieger — 2016</SpecLabel>
      </div>
      <div style={{ marginTop: 26, borderTop: `1px solid ${EL.line}`, paddingTop: 18,
        display: 'grid', gridTemplateColumns: '120px 1fr', gap: 16 }}>
        <SpecLabel color={EL.ink}>Coach's read</SpecLabel>
        <p style={{ margin: 0, fontFamily: EL_HEAD, fontWeight: 500, fontSize: 14.5,
          lineHeight: 1.6, color: EL.sub }}>
          Don't cram chest into one brutal Monday. Split the same sets across two days
          and you grow faster for free — which is exactly how your week below is built.
        </p>
      </div>
    </div>
  );
}

// ── 02 / LAST WEEK ───────────────────────────────────────
function RecapEL({ accent, deload }) {
  const stats = [
    { n: '4', d: '/4', l: 'Sessions' },
    { n: '+7.5', d: 'kg', l: 'Load added', hot: true },
    { n: '0', d: '', l: 'Skipped' },
  ];
  return (
    <div style={{ background: EL.bone, padding: `30px ${EPAD}px 32px` }}>
      <SectionHead index="02" title="Last Week" right="Wk 06 · Logged" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr' }}>
        {stats.map((s, i) => (
          <div key={i} style={{ borderLeft: i ? `1px solid ${EL.hair}` : 'none',
            paddingLeft: i ? 22 : 0 }}>
            <div style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 54,
              lineHeight: 0.9, color: EL.ink, letterSpacing: '0.01em' }}>
              {s.n}<span style={{ fontSize: 26, color: s.hot ? EL.voltText : EL.faint }}>{s.d}</span>
            </div>
            <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 7 }}>
              {s.hot && <span style={{ width: 7, height: 7, background: accent, display: 'inline-block' }} />}
              <SpecLabel>{s.l}</SpecLabel>
            </div>
          </div>
        ))}
      </div>
      <p style={{ margin: '24px 0 0', fontFamily: EL_HEAD, fontWeight: 500, fontSize: 14,
        lineHeight: 1.6, color: EL.sub, borderTop: `1px solid ${EL.line}`, paddingTop: 16 }}>
        {deload
          ? 'Six straight weeks of progression in the log. That earned this deload — recover like it\u2019s part of the program, because it is.'
          : <span>Biggest jump: <strong style={{ color: EL.ink, fontWeight: 700 }}>squat to 90 kg</strong>. Momentum's real — keep the form tight.</span>}
      </p>
    </div>
  );
}

// ── 03 / THE WEEK ────────────────────────────────────────
function PlanEL({ accent, deload }) {
  const days = [
    { d: 'MON', s: 'Upper — Push + Pull',      k: 'Bench Press',   w: '70',  u: 'kg' },
    { d: 'WED', s: 'Lower — All-in',           k: 'Barbell Squat', w: '90',  u: 'kg' },
    { d: 'FRI', s: 'Cali — Shoulders + Chest', k: 'Machine Press', w: '55',  u: 'kg' },
    { d: 'SAT', s: 'Deadlift — Back + Quads',  k: 'Deadlift',      w: '100', u: 'kg' },
  ];
  return (
    <div style={{ background: EL.paper, padding: `30px ${EPAD}px 34px` }}>
      <SectionHead index="03" title="The Week" right={deload ? 'Deload — ½ volume' : 'Progression — Wk 07'} />
      <div style={{ display: 'grid', gridTemplateColumns: '56px 1fr auto', columnGap: 18,
        paddingBottom: 9, borderBottom: `1px solid ${EL.ink}` }}>
        <SpecLabel>Day</SpecLabel>
        <SpecLabel>Session · Top set</SpecLabel>
        <SpecLabel>Load</SpecLabel>
      </div>
      {days.map((x, i) => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: '56px 1fr auto',
          columnGap: 18, alignItems: 'center', padding: '14px 0',
          borderBottom: `1px solid ${EL.line}` }}>
          <span style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 27,
            color: EL.ink, lineHeight: 1, letterSpacing: '0.03em' }}>{x.d}</span>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontFamily: EL_HEAD, fontWeight: 700, fontSize: 14, color: EL.ink }}>{x.s}</div>
            <div style={{ marginTop: 3, fontFamily: EL_MONO, fontSize: 10.5,
              letterSpacing: '0.05em', color: EL.faint }}>
              {x.k}{deload && <span style={{ color: EL.voltText, fontWeight: 600 }}>{' '}— ½ sets</span>}
            </div>
          </div>
          <div style={{ textAlign: 'right', fontFamily: EL_MONO, fontSize: 13,
            fontWeight: 600, color: EL.ink, whiteSpace: 'nowrap' }}>
            {x.w}<span style={{ color: EL.faint, fontWeight: 400 }}> {x.u}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── CTA — the one volt moment ────────────────────────────
function CtaEL({ accent }) {
  return (
    <div style={{ background: EL.paper, padding: `6px ${EPAD}px 40px` }}>
      <a href="#" style={{ textDecoration: 'none', display: 'block' }}>
        <div style={{ background: accent, padding: '22px 26px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 30,
            color: EL.ink, lineHeight: 1, letterSpacing: '0.02em' }}>
            GET THE PLAN
          </span>
          <span style={{ fontFamily: EL_MONO, fontSize: 11, fontWeight: 600,
            letterSpacing: '0.18em', color: 'rgba(21,20,15,.75)' }}>PDF — A4 ↓</span>
        </div>
      </a>
      <div style={{ marginTop: 12, textAlign: 'center' }}>
        <SpecLabel>Print it · Glue it in the notebook · Beat last week</SpecLabel>
      </div>
    </div>
  );
}

// ── FOOTER ───────────────────────────────────────────────
function FooterEL({ accent, name = 'LIGHT WEIGHT' }) {
  return (
    <div style={{ background: EL.ink, padding: `30px ${EPAD}px 34px` }}>
      <div style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 30, color: EL.white,
        letterSpacing: '0.02em', lineHeight: 1 }}>
        {name}<span style={{ color: accent }}>.</span>
      </div>
      <p style={{ margin: '14px 0 0', fontFamily: EL_HEAD, fontWeight: 500, fontSize: 12.5,
        lineHeight: 1.6, color: 'rgba(245,243,236,.6)', maxWidth: 390 }}>
        Reply with a voice memo after each session — tell me what moved and what hurt.
        Next Sunday's loads adjust to what you say.
      </p>
      <div style={{ marginTop: 22, borderTop: '1px solid rgba(245,243,236,.18)', paddingTop: 14,
        display: 'flex', gap: 18, flexWrap: 'wrap' }}>
        <SpecLabel color="rgba(245,243,236,.45)">Unsubscribe</SpecLabel>
        <SpecLabel color="rgba(245,243,236,.45)">Archive</SpecLabel>
        <SpecLabel color="rgba(245,243,236,.45)">Sent every Sunday</SpecLabel>
      </div>
    </div>
  );
}

Object.assign(window, {
  EL, EL_DISPLAY, EL_HEAD, EL_MONO, EPAD,
  SpecLabel, SectionHead,
  MastheadEL, DeloadStrip, HeroEL, ScienceEL, RecapEL, PlanEL, CtaEL, FooterEL,
});
