/* identity-boards.jsx — name/wordmark options + brand system card.
   Depends on newsletter-elevated.jsx (EL palette + font stacks). */

// ── Names & wordmarks board ──────────────────────────────
function WordmarkRow({ accent, name, note, tag, last }) {
  return (
    <div style={{ padding: '30px 40px 28px',
      borderBottom: last ? 'none' : '1px solid rgba(245,243,236,.14)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 14 }}>
        <SpecLabel color="rgba(245,243,236,.45)">{tag}</SpecLabel>
      </div>
      <div style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 64, lineHeight: 0.92,
        color: EL.white, letterSpacing: '0.015em', whiteSpace: 'nowrap' }}>
        {name}<span style={{ color: accent }}>.</span>
      </div>
      <p style={{ margin: '13px 0 0', fontFamily: EL_HEAD, fontWeight: 500, fontSize: 12.5,
        lineHeight: 1.55, color: 'rgba(245,243,236,.55)', maxWidth: 430 }}>
        {note}
      </p>
    </div>
  );
}

function NamesBoard({ accent }) {
  return (
    <div style={{ background: EL.ink, minHeight: '100%' }}>
      <div style={{ height: 3, background: accent }} />
      <div style={{ padding: '20px 40px 6px', display: 'flex', justifyContent: 'space-between' }}>
        <SpecLabel color="rgba(245,243,236,.5)">Name candidates</SpecLabel>
        <SpecLabel color="rgba(245,243,236,.5)">Pick via Tweaks →</SpecLabel>
      </div>
      <WordmarkRow accent={accent} tag="A — Keep" name="LIGHT WEIGHT"
        note="The inside joke stays — it just puts on a serious uniform. Warmth is the brand; the stencil does the heavy lifting." />
      <WordmarkRow accent={accent} tag="B — The principle" name="OVERLOAD"
        note="From progressive overload — the one principle the entire letter runs on. Reads like a lab protocol." />
      <WordmarkRow accent={accent} tag="C — The mechanism" name="TENSION"
        note="Mechanical tension is what actually builds muscle. One word, zero hype." />
      <WordmarkRow accent={accent} tag="D — The math" name="VOLUME" last={true}
        note="Sets × reps × load. The number you and the letter both track week over week." />
    </div>
  );
}

// ── System board ─────────────────────────────────────────
function SysRow({ label, children }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', gap: 18,
      alignItems: 'baseline', padding: '16px 0', borderBottom: `1px solid ${EL.line}` }}>
      <SpecLabel>{label}</SpecLabel>
      <div>{children}</div>
    </div>
  );
}

function SystemBoard({ accent }) {
  return (
    <div style={{ background: EL.paper, minHeight: '100%', padding: '26px 40px 34px' }}>
      <div style={{ borderTop: `1px solid ${EL.ink}`, paddingTop: 12, marginBottom: 6,
        display: 'flex', justifyContent: 'space-between' }}>
        <SpecLabel color={EL.ink}>The system</SpecLabel>
        <SpecLabel>Performance-lab</SpecLabel>
      </div>

      <SysRow label="Display">
        <div style={{ fontFamily: EL_DISPLAY, fontWeight: 800, fontSize: 44, lineHeight: 0.95,
          color: EL.ink, letterSpacing: '0.015em' }}>BIG SHOULDERS STENCIL</div>
        <div style={{ marginTop: 6 }}><SpecLabel>Wordmark · Hero · Stats · Day codes</SpecLabel></div>
      </SysRow>

      <SysRow label="Body">
        <div style={{ fontFamily: EL_HEAD, fontWeight: 700, fontSize: 21, color: EL.ink,
          letterSpacing: '-0.01em' }}>Archivo — headlines &amp; coach's voice</div>
        <div style={{ marginTop: 6 }}><SpecLabel>Warm copy lives here, unchanged</SpecLabel></div>
      </SysRow>

      <SysRow label="Spec">
        <div style={{ fontFamily: EL_MONO, fontSize: 13, fontWeight: 600, color: EL.ink,
          letterSpacing: '0.18em', textTransform: 'uppercase' }}>JetBrains Mono — labels · citations</div>
      </SysRow>

      <SysRow label="Color ration">
        <div style={{ display: 'flex', height: 40 }}>
          <div style={{ flex: '0 0 58%', background: EL.ink }}></div>
          <div style={{ flex: '0 0 38%', background: EL.bone, border: `1px solid ${EL.line}` }}></div>
          <div style={{ flex: '1', background: accent }}></div>
        </div>
        <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between' }}>
          <SpecLabel>Ink 58 · Bone 38 · Volt ≤ 4</SpecLabel>
        </div>
        <p style={{ margin: '10px 0 0', fontFamily: EL_HEAD, fontWeight: 500, fontSize: 12,
          lineHeight: 1.55, color: EL.sub, maxWidth: 420 }}>
          Volt is rationed: one rule, one underline, one block per issue. Scarcity is what
          makes it feel expensive.
        </p>
      </SysRow>

      <SysRow label="Craft rules">
        <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'grid', gap: 7 }}>
          {['Square corners. No shadows. Hairlines do the structure.',
            'Photography runs B&W, full bleed, type set over it.',
            'Sections are numbered like a protocol: 01 / 02 / 03.',
            'Coach\u2019s voice stays warm — the frame around it gets formal.'].map((r, i) => (
            <li key={i} style={{ fontFamily: EL_HEAD, fontWeight: 500, fontSize: 12.5,
              lineHeight: 1.5, color: EL.ink, display: 'flex', gap: 10, alignItems: 'baseline' }}>
              <span style={{ width: 6, height: 6, background: accent, flexShrink: 0,
                display: 'inline-block', transform: 'translateY(-1px)' }}></span>
              {r}
            </li>
          ))}
        </ul>
      </SysRow>
    </div>
  );
}

Object.assign(window, { NamesBoard, SystemBoard, WordmarkRow });
