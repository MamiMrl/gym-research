#!/usr/bin/env python3
"""
Generate beautiful HTML workout plans matching the personal-workout-plan.html design.
"""

import json
from datetime import datetime


class WorkoutHTMLGenerator:
    def __init__(self, output_path="Workout_Plan.html"):
        self.output_path = output_path
        self.html = ""

    def build_html(self, week_data, week_num=1, is_deload=False):
        """
        Build and write HTML workout plan.

        Args:
            week_data: Dict with 'monday', 'wednesday', 'friday', 'saturday' keys
            week_num: Current week number
            is_deload: Whether this is a deload week
        """
        self.week_num = week_num
        self.is_deload = is_deload
        self.week_data = week_data

        self._build_document()
        self._write_file()

        return self.output_path

    def _build_document(self):
        """Build the complete HTML document."""
        self.html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gym Plan — Week {self.week_num}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

  :root {{
    --bvb-yellow: #FDE100;
    --bvb-yellow-dim: #E5CC00;
    --bvb-black: #000000;
    --bvb-charcoal: #1A1A1A;
    --bvb-gray: #2B2B2B;
    --bvb-light: #F5F5F5;
    --bvb-divider: rgba(253, 225, 0, 0.25);
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  @page {{
    size: A4 landscape;
    margin: 10mm 8mm;
  }}

  @media print {{
    body {{ margin: 0; padding: 0; }}
  }}

  html, body {{
    background: #000;
    color: #fff;
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 9.5pt;
    line-height: 1.4;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  /* HERO */
  .hero {{
    background: linear-gradient(135deg, var(--bvb-black) 0%, var(--bvb-charcoal) 100%);
    border: 3px solid var(--bvb-yellow);
    padding: 12mm 8mm 10mm 8mm;
    margin-bottom: 6mm;
    position: relative;
    overflow: hidden;
  }}

  .hero::before {{
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 50%;
    height: 100%;
    background: repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(253,225,0,0.08) 10px, rgba(253,225,0,0.08) 20px);
  }}

  .hero-tag {{
    display: inline-block;
    background: var(--bvb-yellow);
    color: var(--bvb-black);
    padding: 2px 10px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 8pt;
    letter-spacing: 2px;
    margin-bottom: 6mm;
    position: relative;
    z-index: 1;
  }}

  .hero h1 {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 48pt;
    line-height: 0.9;
    color: var(--bvb-yellow);
    letter-spacing: 1px;
    margin-bottom: 3mm;
    position: relative;
    z-index: 1;
    text-transform: uppercase;
  }}

  .hero h1 .accent {{ color: #fff; }}

  .hero-sub {{
    font-family: 'JetBrains Mono', monospace;
    color: #fff;
    font-size: 9pt;
    letter-spacing: 0.5px;
    position: relative;
    z-index: 1;
    margin-bottom: 5mm;
  }}

  .hero-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 4mm;
    position: relative;
    z-index: 1;
    margin-top: 4mm;
  }}

  .stat {{ border-left: 3px solid var(--bvb-yellow); padding-left: 3mm; }}

  .stat-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.5pt;
    color: var(--bvb-yellow);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 1mm;
  }}

  .stat-value {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 16pt;
    color: #fff;
    line-height: 1;
  }}

  /* ALERT */
  .alert {{
    background: var(--bvb-yellow);
    color: var(--bvb-black);
    padding: 4mm 6mm;
    margin-bottom: 6mm;
    font-weight: 700;
    font-size: 8.5pt;
    border-left: 6px solid var(--bvb-black);
    position: relative;
  }}

  .alert::after {{
    content: '⚠';
    position: absolute;
    right: 6mm;
    top: 50%;
    transform: translateY(-50%);
    font-size: 18pt;
    font-weight: 900;
  }}

  /* WEEK */
  .week-section {{ margin-bottom: 6mm; }}

  .week-banner {{
    background: var(--bvb-yellow);
    color: var(--bvb-black);
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22pt;
    letter-spacing: 3px;
    padding: 3mm 6mm;
    margin-bottom: 4mm;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 5px solid var(--bvb-black);
  }}

  .week-banner .week-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9pt;
    font-weight: 700;
    background: var(--bvb-black);
    color: var(--bvb-yellow);
    padding: 2px 10px;
    letter-spacing: 1.5px;
  }}

  .day-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4mm;
  }}

  /* CARD */
  .day-card {{
    background: var(--bvb-charcoal);
    border: 2px solid var(--bvb-yellow);
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  .day-header {{
    background: var(--bvb-yellow);
    color: var(--bvb-black);
    padding: 2mm 3mm;
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 1.5px;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }}

  .day-header .day-num {{ font-size: 14pt; }}
  .day-header .day-title {{ font-size: 10pt; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 8pt; }}

  thead th {{
    background: var(--bvb-black);
    color: var(--bvb-yellow);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 7pt;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 1.5mm 2mm;
    text-align: left;
    border-bottom: 2px solid var(--bvb-yellow);
  }}

  thead th:first-child {{ width: 5mm; text-align: center; }}
  thead th.center {{ text-align: center; }}

  tbody td {{
    padding: 1.5mm 2mm;
    color: #fff;
    border-bottom: 1px solid var(--bvb-divider);
    font-size: 8pt;
  }}

  tbody td.num {{
    color: var(--bvb-yellow);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    text-align: center;
    width: 5mm;
  }}

  tbody td.exercise {{ font-weight: 600; color: #fff; }}
  tbody td.center {{ text-align: center; }}

  tbody td.weight {{
    color: var(--bvb-yellow);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 7.5pt;
  }}

  tbody tr:last-child td {{ border-bottom: none; }}
  tbody tr:nth-child(even) td {{ background: rgba(253, 225, 0, 0.04); }}

  /* REHAB */
  .rehab-section {{
    background: var(--bvb-yellow);
    color: var(--bvb-black);
    padding: 5mm 6mm;
    margin-top: 6mm;
    margin-bottom: 6mm;
    page-break-inside: avoid;
  }}

  .rehab-section h2 {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22pt;
    letter-spacing: 2px;
    margin-bottom: 2mm;
  }}

  .rehab-section .sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    margin-bottom: 4mm;
    font-weight: 600;
  }}

  .rehab-section table {{ background: var(--bvb-black); }}
  .rehab-section thead th {{
    background: var(--bvb-black);
    color: var(--bvb-yellow);
  }}

  /* NOTES */
  .notes {{
    background: var(--bvb-charcoal);
    border-top: 4px solid var(--bvb-yellow);
    border-bottom: 4px solid var(--bvb-yellow);
    padding: 5mm 6mm;
    margin-top: 6mm;
    page-break-inside: avoid;
  }}

  .notes h2 {{
    font-family: 'Bebas Neue', sans-serif;
    color: var(--bvb-yellow);
    font-size: 18pt;
    letter-spacing: 2px;
    margin-bottom: 3mm;
  }}

  .notes ul {{ list-style: none; padding-left: 0; }}
  .notes li {{
    padding: 1.5mm 0 1.5mm 5mm;
    position: relative;
    color: #fff;
    font-size: 8.5pt;
    border-bottom: 1px solid rgba(253, 225, 0, 0.15);
  }}

  .notes li:last-child {{ border-bottom: none; }}
  .notes li::before {{
    content: '▸';
    position: absolute;
    left: 0;
    color: var(--bvb-yellow);
    font-weight: 900;
  }}

  .notes li b {{ color: var(--bvb-yellow); }}

  /* VOLUME RECAP */
  .volume-recap {{
    background: var(--bvb-black);
    border: 2px solid var(--bvb-yellow);
    padding: 4mm 6mm;
    margin-top: 6mm;
    page-break-inside: avoid;
  }}

  .volume-recap h2 {{
    font-family: 'Bebas Neue', sans-serif;
    color: var(--bvb-yellow);
    font-size: 16pt;
    letter-spacing: 2px;
    margin-bottom: 3mm;
  }}

  .volume-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 3mm;
  }}

  .volume-item {{
    text-align: center;
    border: 1px solid var(--bvb-yellow);
    padding: 2mm;
  }}

  .volume-item .muscle {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.5pt;
    color: var(--bvb-yellow);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 1mm;
  }}

  .volume-item .sets {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 18pt;
    color: #fff;
    line-height: 1;
  }}

  .volume-item .label {{ font-size: 6pt; color: #aaa; margin-top: 1mm; }}

  /* END */
  .end-block {{
    text-align: center;
    margin-top: 6mm;
    padding: 4mm;
    border-top: 2px solid var(--bvb-yellow);
  }}

  .end-block .slogan {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 18pt;
    letter-spacing: 4px;
    color: var(--bvb-yellow);
  }}

  .end-block .slogan .dot {{ color: #fff; }}

  @media print {{
    .day-card {{
      border: 1.5px dashed var(--bvb-yellow);
    }}
  }}
</style>
</head>
<body>

{self._build_hero()}
{self._build_alert()}
{self._build_week_section()}
{self._build_rehab_section()}
{self._build_notes_section()}
{self._build_end_block()}

</body>
</html>"""

    def _build_hero(self):
        """Build the hero section."""
        week_label = "WEEK"
        week_desc = f"{self.week_num:02d}"
        if self.is_deload:
            week_label += " (DELOAD)"

        return f"""<section class="hero">
  <span class="hero-tag">// WEEKLY PROGRESSION</span>
  <h1>{week_label}<br><span class="accent">PLAN.</span></h1>
  <div class="hero-sub">STRENGTH · HYPERTROPHY · UPPER/LOWER SPLIT</div>
  <div class="hero-grid">
    <div class="stat"><div class="stat-label">WEEK</div><div class="stat-value">{week_desc}</div></div>
    <div class="stat"><div class="stat-label">SCHEDULE</div><div class="stat-value">2+2</div></div>
    <div class="stat"><div class="stat-label">BODYWEIGHT</div><div class="stat-value">79 kg</div></div>
    <div class="stat"><div class="stat-label">PHASE</div><div class="stat-value">PROGRESSION</div></div>
  </div>
</section>"""

    def _build_alert(self):
        """Build alert section if deload week."""
        if self.is_deload:
            return """<div class="alert">DELOAD WEEK — SAME WEIGHTS, 50–60% VOLUME · STOP 3–4 RIR · FOCUS ON MOVEMENT QUALITY</div>"""
        else:
            return """<div class="alert">SHOULDER REHAB ACTIVE — 45s isometric external rotation hold before MON, FRI, SAT sessions</div>"""

    def _build_week_section(self):
        """Build the week section with day cards."""
        days = [
            ("MON", "UPPER · PUSH + PULL", self.week_data.get('monday', [])),
            ("WED", "LOWER · STRENGTH", self.week_data.get('wednesday', [])),
            ("FRI", "UPPER · SECONDARY", self.week_data.get('friday', [])),
            ("SAT", "LOWER · POWER", self.week_data.get('saturday', [])),
        ]

        html = f"""<section class="week-section">
  <div class="week-banner"><span>WEEK {self.week_num:02d} — DAILY PLAN</span><span class="week-tag">DAYS 1–4</span></div>
  <div class="day-grid">
"""

        for day_num, (day_abbr, day_title, exercises) in enumerate(days, 1):
            html += self._build_day_card(day_num, day_abbr, day_title, exercises)

        html += """  </div>
</section>
"""
        return html

    def _build_day_card(self, day_num, day_abbr, day_title, exercises):
        """Build a single day card."""
        if not isinstance(exercises, dict):
            exercises = {'exercises': exercises} if isinstance(exercises, list) else {'exercises': []}

        exercise_list = exercises.get('exercises', exercises) if isinstance(exercises, dict) else exercises

        table_html = """      <table>
        <thead><tr><th>#</th><th>Exercise</th><th class="center">Sets</th><th class="center">Reps</th><th class="center">Weight</th><th class="center">Rest</th></tr></thead>
        <tbody>
"""

        for ex in exercise_list:
            ex_num = ex.get('num', '—')
            ex_name = ex.get('exercise', '—')
            ex_sets = ex.get('sets', '—')
            ex_reps = ex.get('reps', '—')
            ex_weight = ex.get('weight', '—')
            ex_rest = ex.get('rest', '—')

            table_html += f"""          <tr><td class="num">{ex_num}</td><td class="exercise">{ex_name}</td><td class="center">{ex_sets}</td><td class="center">{ex_reps}</td><td class="weight center">{ex_weight}</td><td class="center">{ex_rest}</td></tr>
"""

        table_html += """        </tbody>
      </table>
"""

        return f"""    <div class="day-card">
      <div class="day-header"><span class="day-num">DAY {day_num:02d}</span><span class="day-title">{day_title}</span></div>
{table_html}    </div>
"""

    def _build_rehab_section(self):
        """Build the rehab section."""
        return """<section class="rehab-section">
  <h2>SHOULDER REHAB · DAILY</h2>
  <div class="sub">// PERFORM BEFORE MON, FRI, SAT SESSIONS — ROOTED IN ISOMETRIC ANALGESIA RESEARCH</div>
  <table>
    <thead><tr><th>#</th><th>Drill</th><th class="center">Sets</th><th class="center">Duration</th><th class="center">Intensity</th><th>Cue</th></tr></thead>
    <tbody>
      <tr><td class="num">1</td><td class="exercise">Cable External Rotation Hold</td><td class="center">5</td><td class="center">45 s</td><td class="weight center">70% MVC</td><td>Pain-free angle, 2 min rest between holds</td></tr>
      <tr><td class="num">2</td><td class="exercise">Wall Slides</td><td class="center">1</td><td class="center">10 reps</td><td class="weight center">light</td><td>Activate scapular upward rotation</td></tr>
      <tr><td class="num">3</td><td class="exercise">Y / T / W Holds (prone)</td><td class="center">1</td><td class="center">20 s ea</td><td class="weight center">BW</td><td>Lower trap, mid trap, rhomboids</td></tr>
    </tbody>
  </table>
</section>
"""

    def _build_notes_section(self):
        """Build the protocol notes section."""
        return """<section class="notes">
  <h2>PROTOCOL NOTES</h2>
  <ul>
    <li><b>Warm-up</b> — 5 min light cardio + dynamic stretches before every session</li>
    <li><b>Compound ramp</b> — empty bar × 10 → 50% × 5 → 70% × 3 → 85% × 1 → working sets</li>
    <li><b>RIR target</b> — 1–2 reps in reserve; failure only on the last set of an isolation lift</li>
    <li><b>Pain during session?</b> — drop the load, run isometric protocol, retest next session</li>
    <li><b>Failed progression?</b> — repeat this week's loads next cycle, retry after</li>
  </ul>
</section>
"""

    def _build_end_block(self):
        """Build the end block with slogan."""
        return """<div class="end-block">
  <div class="slogan">TRAIN HARD<span class="dot"> · </span>RECOVER HARDER<span class="dot"> · </span>KEEP PUSHING</div>
</div>
"""

    def _write_file(self):
        """Write HTML to file."""
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(self.html)
