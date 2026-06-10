/* newsletter-blocks.jsx — low-fi wireframe primitives + blocks for the
   Weekly Science Newsletter. Monochrome greybox on purpose: we are
   validating structure & hierarchy, not visuals. */

// ── palette ──────────────────────────────────────────────
const LF = {
  ink:    '#2c2c2c',   // headings / strong text
  sub:    '#6f6f6f',   // secondary text
  bar:    '#d7d7d7',   // text placeholder bar
  barLite:'#e7e7e7',   // lighter bar
  line:   '#e4e4e4',   // hairline rules
  card:   '#ededed',   // tile fill
  cardBd: '#dcdcdc',   // tile border
  dash:   '#c2c2c2',   // dashed placeholder
  btn:    '#333333',   // wireframe button
  muted:  '#9b9b9b',   // mono annotation labels
  pad:    36,
};
const MONO = '"SF Mono", "JetBrains Mono", ui-monospace, Menlo, monospace';
const SANS = 'Helvetica, "Helvetica Neue", Arial, sans-serif';

// ── primitives ───────────────────────────────────────────
function Bar({ w = '100%', h = 10, c = LF.bar, mt = 0, r = 3 }) {
  return <div style={{ width: w, height: h, background: c, borderRadius: r, marginTop: mt }} />;
}

function Lines({ widths = ['100%', '92%', '70%'], gap = 9, c = LF.barLite, h = 9 }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap }}>
      {widths.map((w, i) => <Bar key={i} w={w} h={h} c={c} />)}
    </div>
  );
}

// little monospace annotation tag that names each structural block
function Tag({ children }) {
  return (
    <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: '0.14em',
      color: LF.muted, textTransform: 'uppercase', marginBottom: 12,
      display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ width: 14, height: 1, background: LF.muted, display: 'inline-block' }} />
      {children}
    </div>
  );
}

function Rule({ my = 0 }) {
  return <div style={{ height: 1, background: LF.line, margin: `${my}px 0` }} />;
}

// section shell with consistent horizontal padding
function Sec({ children, pt = 28, pb = 28, bg = '#fff' }) {
  return <div style={{ padding: `${pt}px ${LF.pad}px ${pb}px`, background: bg }}>{children}</div>;
}

// ── BLOCKS ───────────────────────────────────────────────

function Masthead() {
  return (
    <div style={{ padding: `22px ${LF.pad}px`, background: '#fafafa', borderBottom: `1px solid ${LF.line}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 30, height: 30, background: LF.btn, borderRadius: 6 }} />
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 18, color: LF.ink, letterSpacing: '-0.01em' }}>
            [ Newsletter name ]
          </div>
        </div>
        <div style={{ fontFamily: MONO, fontSize: 11, color: LF.sub, textAlign: 'right', lineHeight: 1.5 }}>
          ISSUE 12<br />SUN · JUN 9
        </div>
      </div>
    </div>
  );
}

// the single big hero science fact
function HeroFact({ compact = false }) {
  return (
    <Sec pt={compact ? 30 : 40} pb={compact ? 30 : 40}>
      <Tag>Science fact of the week</Tag>
      <div style={{ fontFamily: SANS, fontWeight: 800, color: LF.ink, letterSpacing: '-0.02em',
        fontSize: compact ? 30 : 36, lineHeight: 1.12 }}>
        Training a muscle <span style={{ background: '#e6e6e6', padding: '0 4px' }}>2× per week</span> builds
        ~15% more muscle than once — even at identical weekly volume.
      </div>
      <div style={{ marginTop: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ width: 22, height: 1, background: LF.muted }} />
        <span style={{ fontFamily: MONO, fontSize: 11, color: LF.sub }}>
          Schoenfeld et al. (2016) · meta-analysis
        </span>
      </div>
      {!compact && <div style={{ marginTop: 20 }}><Lines widths={['100%', '96%', '58%']} /></div>}
    </Sec>
  );
}

// last week recap — stat tiles + a line of context
function Recap({ strip = false }) {
  const tiles = [
    { n: '4 / 4', l: 'sessions done' },
    { n: '+7.5', l: 'kg added' },
    { n: '0', l: 'skipped' },
  ];
  return (
    <Sec pt={strip ? 22 : 26} pb={strip ? 22 : 26} bg={strip ? '#fafafa' : '#fff'}>
      <Tag>Last week · recap</Tag>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        {tiles.map((t, i) => (
          <div key={i} style={{ background: LF.card, border: `1px solid ${LF.cardBd}`,
            borderRadius: 8, padding: '14px 12px', textAlign: 'center' }}>
            <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 22, color: LF.ink }}>{t.n}</div>
            <div style={{ fontFamily: MONO, fontSize: 9.5, color: LF.sub, marginTop: 5,
              letterSpacing: '0.06em', textTransform: 'uppercase' }}>{t.l}</div>
          </div>
        ))}
      </div>
      {!strip && <div style={{ marginTop: 16 }}><Lines widths={['100%', '74%']} /></div>}
    </Sec>
  );
}

// this week's plan teaser — 4 day rows with key lift
function PlanPreview({ flush = false }) {
  const days = [
    { d: 'MON', s: 'Upper · Push + Pull',   k: 'Bench Press — 70 kg' },
    { d: 'WED', s: 'Lower · All-in',        k: 'Barbell Squat — 90 kg' },
    { d: 'FRI', s: 'Cali · Shoulders+Chest',k: 'Machine Press — 55 kg' },
    { d: 'SAT', s: 'Deadlift · Back+Quads', k: 'Deadlift — 100 kg' },
  ];
  return (
    <Sec pt={flush ? 24 : 28} pb={flush ? 18 : 28}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 4 }}>
        <Tag>This week's plan</Tag>
        <span style={{ fontFamily: MONO, fontSize: 10, color: LF.muted }}>UPPER/LOWER · 4 DAYS</span>
      </div>
      <div style={{ border: `1px solid ${LF.line}`, borderRadius: 10, overflow: 'hidden' }}>
        {days.map((x, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14,
            padding: '13px 14px', borderTop: i ? `1px solid ${LF.line}` : 'none' }}>
            <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700, color: LF.ink,
              width: 38, flexShrink: 0 }}>{x.d}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: SANS, fontSize: 13, fontWeight: 700, color: LF.ink }}>{x.s}</div>
              <div style={{ fontFamily: MONO, fontSize: 10.5, color: LF.sub, marginTop: 4 }}>{x.k}</div>
            </div>
            <div style={{ width: 18, height: 18, borderRadius: 4, border: `1px dashed ${LF.dash}`, flexShrink: 0 }} />
          </div>
        ))}
      </div>
    </Sec>
  );
}

// the primary download CTA
function Cta({ tight = false }) {
  return (
    <Sec pt={tight ? 6 : 8} pb={tight ? 24 : 30}>
      <div style={{ width: '100%', background: LF.btn, borderRadius: 10,
        padding: '18px 20px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
        <span style={{ width: 16, height: 16, borderRadius: 3, border: '2px solid #fff', opacity: 0.9,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: '#fff' }}>↓</span>
        <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 15, color: '#fff', letterSpacing: '0.01em' }}>
          Download this week's plan
        </span>
      </div>
      <div style={{ textAlign: 'center', marginTop: 12 }}>
        <span style={{ fontFamily: MONO, fontSize: 10.5, color: LF.muted }}>
          PDF · A4 · print &amp; glue into your notebook
        </span>
      </div>
    </Sec>
  );
}

function Footer() {
  return (
    <div style={{ padding: `24px ${LF.pad}px 30px`, background: '#fafafa', borderTop: `1px solid ${LF.line}` }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
        <Bar w="42%" h={8} c={LF.barLite} />
        <Bar w="30%" h={8} c={LF.barLite} />
        <div style={{ fontFamily: MONO, fontSize: 10, color: LF.muted, marginTop: 8 }}>
          UNSUBSCRIBE · VIEW ARCHIVE
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  LF, MONO, SANS,
  Bar, Lines, Tag, Rule, Sec,
  Masthead, HeroFact, Recap, PlanPreview, Cta, Footer,
});
