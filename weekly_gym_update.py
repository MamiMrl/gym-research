#!/usr/bin/env python3
"""
weekly_gym_update.py — Weekly gym progress orchestration script.

The Claude scheduled agent calls this script each Sunday, then handles
Gmail (read reply / send email) via MCP tools using this script's JSON output.

Usage:
  python3 weekly_gym_update.py init                    # seed progress_log.json
  python3 weekly_gym_update.py status                  # print current state
  python3 weekly_gym_update.py process                 # first run (no reply)
  python3 weekly_gym_update.py process --reply "..."   # with email reply body
  python3 weekly_gym_update.py process --no-reply      # reminder (no changes)
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

PROGRESS_LOG = Path('/Users/neu/Downloads/gym-research/progress_log.json')
PDF_DIR = Path('/Users/neu/Downloads/gym-research')

DAYS = ['MON', 'WED', 'FRI', 'SAT']
DAY_KEY_MAP = {'MON': 'monday', 'WED': 'wednesday', 'FRI': 'friday', 'SAT': 'saturday'}
DAY_LABEL_MAP = {'MON': 'Upper A', 'WED': 'Lower A', 'FRI': 'Upper B', 'SAT': 'Lower B'}

DAY_SKILLS = {
    'monday':    'Chest-to-Wall Handstand (30 sec)',
    'wednesday': 'Pike Push-Up Progression (incline 45°, 8 reps)',
    'friday':    'Muscle-Up Progression (jumping assist, 5 reps)',
    'saturday':  'Chest-to-Wall Handstand (45 sec)',
}

WEIGHT_INCREMENTS = {
    'barbell':    2.5,
    'dumbbell':   1.0,
    'bw_weighted': 1.25,
    'bw_only':    0.0,
    'skip':       0.0,
    'machine':    2.5,
    'cable_side': 2.5,
}

# Deload protocol (per Gym-planning.md): SAME weights, 50-60% volume reduction
# 3→2 sets ≈ 67% volume kept (close enough), 4→2 = 50% — both within the 50-60% target
DELOAD_SETS_REDUCTION = {'3': '2', '4': '2', '2': '1'}

# (pattern, display_name) — word boundaries prevent "deadlift" matching "\bdead\b", etc.
# Signals derived from: Gym-planning.md (joint pain = deload trigger),
# Dupuy 2018 (fatigue markers), Coffey & Hawley (accumulated fatigue signals)
FATIGUE_KEYWORDS = [
    (r'\btired\b',      'tired'),
    (r'\bexhausted\b',  'exhausted'),
    (r'joint pain',     'joint pain'),
    (r'joint ache',     'joint ache'),
    (r'\bpain\b',       'pain'),
    (r'\bfailed\b',     'failed'),
    (r'no energy',      'no energy'),
    (r'\bhurt\b',       'hurt'),
    (r'\bdead\b',       'dead'),
    (r'burned out',     'burned out'),
    (r'very sore',      'very sore'),
    (r'still sore',     'still sore'),
    (r'always sore',    'always sore'),
    (r"couldn't",       "couldn't"),
    (r'\bdeload\b',     'deload'),
    (r'\bstruggling\b', 'struggling'),
    (r'\bwrecked\b',    'wrecked'),
    (r'no strength',    'no strength'),
    (r'feeling weak',   'feeling weak'),
]


# ── JSON I/O ──────────────────────────────────────────────────────────────────

def load_progress() -> dict:
    with open(PROGRESS_LOG) as f:
        return json.load(f)


def save_progress(data: dict) -> None:
    with open(PROGRESS_LOG, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Weight helpers ────────────────────────────────────────────────────────────

def parse_weight_string(weight: str) -> tuple:
    """Return (weight_type, weight_kg) from a display weight string."""
    w = weight.strip()

    if w.upper() == 'BW':
        return 'bw_only', None

    if re.match(r'(?i)start\s+moderate|moderate', w):
        return 'skip', None

    bw_match = re.match(r'(?i)BW\s*\+\s*([\d.]+)\s*kg', w)
    if bw_match:
        return 'bw_weighted', float(bw_match.group(1))

    db_match = re.match(r'([\d.]+)\s*kg/DB', w, re.IGNORECASE)
    if db_match:
        return 'dumbbell', float(db_match.group(1))

    side_match = re.match(r'([\d.]+)\s*kg/side', w, re.IGNORECASE)
    if side_match:
        return 'cable_side', float(side_match.group(1))

    kg_match = re.match(r'([\d.]+)\s*kg$', w)
    if kg_match:
        return 'barbell', float(kg_match.group(1))

    return 'skip', None


def format_weight_string(kg: float, weight_type: str, original: str) -> str:
    """Reconstruct display string from numeric kg value and type."""
    def fmt(v):
        return str(int(v)) if v == int(v) else str(round(v, 2))

    if weight_type == 'barbell':
        return f"{fmt(kg)} kg"
    elif weight_type == 'dumbbell':
        return f"{fmt(kg)} kg/DB"
    elif weight_type == 'bw_weighted':
        return f"BW + {fmt(kg)} kg"
    elif weight_type == 'cable_side':
        return f"{fmt(kg)} kg/side"
    elif weight_type == 'machine':
        return f"{fmt(kg)} kg"
    else:
        return original


# ── PDF data builder ──────────────────────────────────────────────────────────

def build_week_data(progress: dict, is_deload: bool = False) -> dict:
    """Build the exercise dict that generate_workout_pdf.py expects."""
    week_data = {}
    for day_key, exercises in progress['exercises'].items():
        day_exercises = []
        for ex in exercises:
            ex_copy = {
                'num': ex['num'],
                'exercise': ex['exercise'],
                'sets': ex['sets'],
                'reps': ex['reps'],
                'weight': ex['weight'],
                'rest': ex['rest'],
            }
            if is_deload:
                # Same weights, reduced sets (50-60% volume per Gym-planning.md)
                ex_copy['sets'] = DELOAD_SETS_REDUCTION.get(str(ex['sets']), str(ex['sets']))
            day_exercises.append(ex_copy)
        week_data[day_key] = {
            'skill': DAY_SKILLS[day_key],
            'exercises': day_exercises,
        }
    return week_data


# ── Reply parser ──────────────────────────────────────────────────────────────

def parse_reply(email_body: str) -> dict:
    """
    Parse email reply body into per-day responses.
    Returns dict like: {'MON': {'action': '+', 'comment': '...'}, ...}
    """
    result = {}
    pattern = re.compile(
        r'^(MON|WED|FRI|SAT)\s*:\s*(\+|-|stay)\s*\|?\s*(.*)',
        re.IGNORECASE | re.MULTILINE,
    )
    for match in pattern.finditer(email_body):
        day = match.group(1).upper()
        action = match.group(2).strip()
        comment = match.group(3).strip()
        if action == '+':
            action = '+'
        elif action == '-':
            action = '-'
        else:
            action = 'stay'
        result[day] = {'action': action, 'comment': comment}
    return result


# ── Weight updater ────────────────────────────────────────────────────────────

def update_weights(progress: dict, parsed_reply: dict) -> dict:
    """Apply +/-/stay responses to all trackable exercises."""
    week_num = progress['meta']['current_week']
    for day_abbrev, day_key in DAY_KEY_MAP.items():
        if day_abbrev not in parsed_reply:
            continue
        action = parsed_reply[day_abbrev]['action']
        if action == 'stay':
            for ex in progress['exercises'][day_key]:
                ex['history'].append({
                    'week': week_num,
                    'weight': ex['weight'],
                    'weight_kg': ex.get('weight_kg'),
                    'action': 'stay',
                })
            continue
        direction = 1 if action == '+' else -1
        for ex in progress['exercises'][day_key]:
            wtype = ex.get('weight_type', 'skip')
            increment = WEIGHT_INCREMENTS.get(wtype, 0.0)
            if increment == 0.0:
                continue
            old_kg = ex['weight_kg']
            new_kg = round(old_kg + direction * increment, 2)
            new_kg = max(new_kg, 0.0)
            ex['weight_kg'] = new_kg
            ex['weight'] = format_weight_string(new_kg, wtype, ex['weight'])
            ex['history'].append({
                'week': week_num,
                'weight': ex['weight'],
                'weight_kg': new_kg,
                'action': 'increase' if direction == 1 else 'decrease',
            })
    return progress


# ── Deload detection ──────────────────────────────────────────────────────────

def detect_deload(progress: dict, parsed_reply: dict | None) -> tuple:
    """Return (should_deload: bool, reason: str | None)."""
    fatigue = progress['fatigue_tracking']
    deload_info = progress['deload']

    # Hard cap: 6 consecutive progression weeks (user's plan: deload every 4-8 wks;
    # research: 8 wks at high volume approaches overreaching — use 6 as midpoint)
    if deload_info['consecutive_progression_weeks'] >= 6:
        return True, "6 consecutive weeks of progression — scheduled deload (4-8 week cycle)"

    if parsed_reply is None:
        return False, None

    # Check for fatigue keywords or explicit deload request in comments
    all_comments = ' '.join(
        r.get('comment', '').lower() for r in parsed_reply.values()
    )
    for pattern, display in FATIGUE_KEYWORDS:
        if re.search(pattern, all_comments):
            return True, f"Fatigue signal detected in your comments (\"{display}\")"

    # 3+ consecutive weeks with zero progression
    if fatigue['consecutive_no_progress_weeks'] >= 3:
        return True, "3 consecutive weeks with no progression"

    # 2+ consecutive weeks of decline on the same day
    for day, count in fatigue['days_consecutive_decline'].items():
        if count >= 2:
            return True, f"2 consecutive weeks of decline on {day}"

    return False, None


def update_fatigue_counters(progress: dict, parsed_reply: dict | None, deload_triggered: bool) -> dict:
    """Update rolling fatigue and progression counters."""
    fatigue = progress['fatigue_tracking']
    deload_info = progress['deload']

    if deload_triggered:
        fatigue['consecutive_no_progress_weeks'] = 0
        fatigue['days_consecutive_decline'] = {d: 0 for d in DAYS}
        deload_info['consecutive_progression_weeks'] = 0
        deload_info['weeks_since_last_deload'] = 0
        deload_info['last_deload_date'] = date.today().isoformat()
        deload_info['deload_count_total'] += 1
        return progress

    deload_info['weeks_since_last_deload'] = deload_info.get('weeks_since_last_deload', 0) + 1

    if parsed_reply is None:
        return progress

    plus_count = sum(1 for r in parsed_reply.values() if r['action'] == '+')

    if plus_count == 0:
        fatigue['consecutive_no_progress_weeks'] += 1
    else:
        fatigue['consecutive_no_progress_weeks'] = 0
        deload_info['consecutive_progression_weeks'] += 1

    for day in DAYS:
        if day in parsed_reply:
            if parsed_reply[day]['action'] == '-':
                fatigue['days_consecutive_decline'][day] = (
                    fatigue['days_consecutive_decline'].get(day, 0) + 1
                )
            else:
                fatigue['days_consecutive_decline'][day] = 0

    return progress


def apply_deload_to_progress(progress: dict, reason: str) -> dict:
    """Flag deload week in JSON. Weights stay the same — only sets are reduced
    in the PDF (handled by build_week_data). Protocol per Gym-planning.md:
    same loads, 50-60% volume, more RIR."""
    progress['deload']['is_deload_week'] = True
    progress['deload']['deload_history'].append({
        'date': date.today().isoformat(),
        'week': progress['meta']['current_week'],
        'reason': reason,
    })
    week_num = progress['meta']['current_week']
    for day_key, exercises in progress['exercises'].items():
        for ex in exercises:
            ex['history'].append({
                'week': week_num,
                'weight': ex['weight'],
                'weight_kg': ex.get('weight_kg'),
                'action': 'deload',
            })
    return progress


# ── Progress summary ──────────────────────────────────────────────────────────

def build_progress_summary(progress: dict, parsed_reply: dict | None, is_deload: bool, deload_reason: str | None) -> str:
    lines = []

    if parsed_reply is None:
        lines.append("No reply was received for last week.")
    else:
        plus_days  = [d for d, r in parsed_reply.items() if r['action'] == '+']
        minus_days = [d for d, r in parsed_reply.items() if r['action'] == '-']
        stay_days  = [d for d, r in parsed_reply.items() if r['action'] == 'stay']

        if plus_days:
            lines.append(f"Progression: {', '.join(plus_days)} — weights increased next week.")
        if stay_days:
            lines.append(f"Held steady: {', '.join(stay_days)}.")
        if minus_days:
            lines.append(f"Backed off: {', '.join(minus_days)} — weights decreased next week.")

        for day, reply in parsed_reply.items():
            if reply.get('comment'):
                lines.append(f"  {day}: \"{reply['comment']}\"")

    if is_deload:
        lines.append(f"\n⚠ DELOAD TRIGGERED — {deload_reason}")
        lines.append("Same weights, ~50% sets, 3-4 RIR. Let joints and CNS recover.")
    else:
        consec = progress['deload']['consecutive_progression_weeks']
        if consec > 0:
            lines.append(f"\nConsecutive progression weeks: {consec}/8")

    return '\n'.join(lines)


# ── History ───────────────────────────────────────────────────────────────────

def append_week_to_history(progress: dict, parsed_reply: dict | None, is_deload: bool, deload_reason: str | None) -> dict:
    entry = {
        'week': progress['meta']['current_week'],
        'date': date.today().isoformat(),
        'reply_found': parsed_reply is not None,
        'responses': {},
        'comments': {},
        'deload_triggered': is_deload,
        'deload_reason': deload_reason,
        'plus_count': 0,
        'minus_count': 0,
        'stay_count': 0,
    }
    if parsed_reply:
        for day, reply in parsed_reply.items():
            entry['responses'][day] = reply['action']
            entry['comments'][day] = reply.get('comment', '')
        entry['plus_count']  = sum(1 for r in parsed_reply.values() if r['action'] == '+')
        entry['minus_count'] = sum(1 for r in parsed_reply.values() if r['action'] == '-')
        entry['stay_count']  = sum(1 for r in parsed_reply.values() if r['action'] == 'stay')
    progress['week_history'].append(entry)
    return progress


def advance_week(progress: dict) -> dict:
    progress['meta']['current_week'] += 1
    progress['meta']['last_run_date'] = date.today().isoformat()
    progress['deload']['is_deload_week'] = False
    return progress


# ── Email content ─────────────────────────────────────────────────────────────

def build_email_subject(week_num: int, is_deload: bool, is_reminder: bool) -> str:
    if is_reminder:
        return f"[REMINDER] Week {week_num} Gym Plan — Reply with your session scores"
    if is_deload:
        return f"Week {week_num} Gym Plan — DELOAD WEEK"
    return f"Week {week_num} Gym Plan — Upper/Lower Split"


def build_email_body(summary: str, week_num: int, is_deload: bool) -> str:
    """Build plain text intro/outro that wraps the HTML workout plan in the email.

    The full HTML workout (BVB dark theme) is embedded between the intro
    and the reply instructions by the routine_agent when composing the email.
    """
    deload_notice = ""
    if is_deload:
        deload_notice = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ DELOAD WEEK — Same weights, ~50% sets, 3-4 RIR.
Focus on movement quality, joints, and CNS recovery.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return f"""Hey Berke,

Week {week_num} workout plan below — embedded HTML renders inline; you can also print it directly to PDF from Gmail.
{deload_notice}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LAST WEEK RECAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REPLY WITH YOUR SCORES for this week:
  + = increase weights next week
  - = decrease weights next week
  stay = keep the same
  Add a comment after | (optional but helpful)

MON: [+/-/stay] | [optional comment]
WED: [+/-/stay] | [optional comment]
FRI: [+/-/stay] | [optional comment]
SAT: [+/-/stay] | [optional comment]

Example:
MON: + | Bench felt strong, had energy left
WED: stay | Quads are still recovering
FRI: - | Shoulder was acting up
SAT: + | Great session
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Train hard.
"""


# ── PDF generator ─────────────────────────────────────────────────────────────

def generate_pdf(progress: dict, week_num: int, is_deload: bool) -> str:
    """Generate PDF and return its path. Suppresses generator's stdout
    prints so the only thing on stdout is our JSON output."""
    sys.path.insert(0, str(PDF_DIR))
    from generate_workout_pdf import WorkoutPDFGenerator
    import contextlib, io

    output_path = str(PDF_DIR / f'Workout_Plan_Week_{week_num}.pdf')
    week_data = build_week_data(progress, is_deload=is_deload)
    generator = WorkoutPDFGenerator(output_path)
    # Redirect noisy "✅ PDF generated" prints to stderr so stdout = JSON only
    with contextlib.redirect_stdout(sys.stderr):
        generator.build_pdf(week_data=week_data, week_num=week_num, is_deload=is_deload)
    return output_path


# ── HTML generator ────────────────────────────────────────────────────────────

def generate_html(progress: dict, week_num: int, is_deload: bool) -> tuple:
    """Generate HTML workout file and return (path, content_string)."""
    sys.path.insert(0, str(PDF_DIR))
    from generate_workout_html import WorkoutHTMLGenerator

    output_path = str(PDF_DIR / f'Workout_Plan_Week_{week_num}.html')
    week_data = build_week_data(progress, is_deload=is_deload)
    generator = WorkoutHTMLGenerator(output_path)
    generator.build_html(week_data=week_data, week_num=week_num, is_deload=is_deload)

    with open(output_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    return output_path, html_content


# ── Init ──────────────────────────────────────────────────────────────────────

def _init_progress_log() -> None:
    """Seed progress_log.json from the Week 1 hardcoded data."""
    sys.path.insert(0, str(PDF_DIR))
    from generate_workout_pdf import WorkoutPDFGenerator

    raw = WorkoutPDFGenerator._get_workout_data()
    exercises = {}
    for day_key, day_data in raw.items():
        exercises[day_key] = []
        for ex in day_data['exercises']:
            wtype, wkg = parse_weight_string(ex['weight'])
            exercises[day_key].append({
                'num':         ex['num'],
                'exercise':    ex['exercise'],
                'sets':        ex['sets'],
                'reps':        ex['reps'],
                'weight':      ex['weight'],
                'weight_kg':   wkg,
                'weight_type': wtype,
                'rest':        ex['rest'],
                'history': [{
                    'week':      1,
                    'weight':    ex['weight'],
                    'weight_kg': wkg,
                    'action':    'initial',
                }],
            })

    progress = {
        'meta': {
            'current_week':       1,
            'cycle_start_date':   date.today().isoformat(),
            'last_run_date':      None,
            'last_email_sent_date': None,
            'last_email_subject': None,
            'is_first_run':       True,
        },
        'deload': {
            'is_deload_week':               False,
            'last_deload_date':             None,
            'deload_count_total':           0,
            'weeks_since_last_deload':      0,
            'consecutive_progression_weeks': 0,
            'deload_history':               [],
        },
        'fatigue_tracking': {
            'consecutive_no_progress_weeks': 0,
            'days_consecutive_decline': {'MON': 0, 'WED': 0, 'FRI': 0, 'SAT': 0},
        },
        'exercises':    exercises,
        'week_history': [],
    }
    save_progress(progress)
    print(f"Initialized {PROGRESS_LOG}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('init')
    subparsers.add_parser('status')

    proc = subparsers.add_parser('process')
    proc.add_argument('--reply', type=str, default=None)
    proc.add_argument('--no-reply', action='store_true')

    args = parser.parse_args()

    if args.command == 'init':
        _init_progress_log()
        return

    if args.command == 'status':
        progress = load_progress()
        print(json.dumps({
            'current_week':                  progress['meta']['current_week'],
            'is_first_run':                  progress['meta']['is_first_run'],
            'last_email_sent_date':          progress['meta']['last_email_sent_date'],
            'consecutive_progression_weeks': progress['deload']['consecutive_progression_weeks'],
            'consecutive_no_progress_weeks': progress['fatigue_tracking']['consecutive_no_progress_weeks'],
            'is_deload_week':                progress['deload']['is_deload_week'],
        }, indent=2))
        return

    # ── process ──
    progress = load_progress()
    is_first_run = progress['meta'].get('is_first_run', False)
    week_num     = progress['meta']['current_week']
    is_reminder  = getattr(args, 'no_reply', False)

    if is_first_run:
        parsed_reply   = None
        should_deload  = False
        deload_reason  = None
        progress['meta']['is_first_run'] = False
        save_progress(progress)
    elif is_reminder:
        parsed_reply  = None
        should_deload = False
        deload_reason = None
    else:
        # Read reply from file if body was too long for arg
        reply_body = args.reply
        if reply_body and reply_body.startswith('@'):
            tmp_path = reply_body[1:]
            with open(tmp_path) as f:
                reply_body = f.read()

        parsed_reply = parse_reply(reply_body) if reply_body else None
        should_deload, deload_reason = detect_deload(progress, parsed_reply)

        if should_deload:
            progress = apply_deload_to_progress(progress, deload_reason)
        elif parsed_reply:
            progress = update_weights(progress, parsed_reply)

        progress = update_fatigue_counters(progress, parsed_reply, should_deload)
        progress = append_week_to_history(progress, parsed_reply, should_deload, deload_reason)
        progress = advance_week(progress)
        save_progress(progress)
        week_num = progress['meta']['current_week']

    pdf_path = generate_pdf(progress, week_num, should_deload)
    html_path, html_content = generate_html(progress, week_num, should_deload)
    summary  = build_progress_summary(progress, parsed_reply, should_deload, deload_reason)
    subject  = build_email_subject(week_num, should_deload, is_reminder)
    body     = build_email_body(summary, week_num, should_deload)

    result = {
        'mode':             'first_run' if is_first_run else ('reminder' if is_reminder else 'reply_found'),
        'week_num':         week_num,
        'pdf_path':         pdf_path,
        'html_path':        html_path,
        'html_content':     html_content,
        'progress_summary': summary,
        'is_deload':        should_deload,
        'deload_reason':    deload_reason,
        'subject':          subject,
        'email_body':       body,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
