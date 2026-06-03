#!/usr/bin/env python3
"""
Generate print-ready single-page workout PDF with 4 workout cards (current week only).
2x2 grid layout on A4 with readable fonts and handwritten notes section.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import os


# Layout dimensions (A4 single page)
PAGE_WIDTH = 210 * mm
PAGE_HEIGHT = 297 * mm
PAGE_MARGIN = 5 * mm
CARD_WIDTH = 95 * mm
GRID_COL_WIDTH = 100 * mm

# Table dimensions
NOTES_ROW_HEIGHT = 6 * mm
NOTES_ROW_COUNT = 3
SKILL_SPACER = 0.5 * mm
TABLE_SPACER = 1 * mm

# Colors
COLOR_HEADER_BG = HexColor('#3498db')
COLOR_HEADER_BORDER = HexColor('#2c3e50')
COLOR_ROW_ALT = HexColor('#ecf0f1')
COLOR_BORDER = HexColor('#bdc3c7')
COLOR_DIVIDER = HexColor('#cccccc')
COLOR_CUT_LINE = HexColor('#aaaaaa')
COLOR_TEXT_DARK = HexColor('#1a1a1a')
COLOR_TEXT_NORMAL = HexColor('#2c3e50')
COLOR_TEXT_META = HexColor('#666666')

# Font sizes
FONT_SIZE_TITLE = 11
FONT_SIZE_DAY = 10
FONT_SIZE_TABLE = 8
FONT_SIZE_META = 7
FONT_SIZE_CUT_LINE = 8

# Spacing (table padding)
PADDING_SMALL = 0.5
PADDING_NORMAL = 1.5
BORDER_WIDTH_NORMAL = 0.5
BORDER_WIDTH_HEADER = 1


class WorkoutPDFGenerator:
    def __init__(self, output_path: str) -> None:
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self.title_style = self._create_style(
            'CustomTitle',
            parent_name='Heading1',
            font_size=FONT_SIZE_TITLE,
            color=COLOR_TEXT_DARK,
            font_name='Helvetica-Bold',
        )
        self.day_style = self._create_style(
            'DayStyle',
            parent_name='Heading2',
            font_size=FONT_SIZE_DAY,
            color=COLOR_TEXT_NORMAL,
            font_name='Helvetica-Bold',
            space_after=0.5,
        )
        self.meta_style = self._create_style(
            'MetaStyle',
            parent_name='Normal',
            font_size=FONT_SIZE_META,
            color=COLOR_TEXT_META,
        )

    def _create_style(
        self,
        name: str,
        parent_name: str,
        font_size: int,
        color: HexColor,
        font_name: str = 'Helvetica',
        space_after: float = 0,
    ) -> ParagraphStyle:
        """Create a ParagraphStyle with common defaults."""
        return ParagraphStyle(
            name,
            parent=self.styles[parent_name],
            fontSize=font_size,
            textColor=color,
            spaceAfter=space_after,
            fontName=font_name,
        )

    def create_workout_table(self, day_data: dict) -> Table:
        """Create a readable workout table for a single day."""
        headers = ['#', 'Exercise', 'Sets', 'Reps', 'Weight', 'Rest']
        data = [
            [Paragraph(f'<b>{h}</b>', self.meta_style) for h in headers]
        ]

        for ex in day_data['exercises']:
            data.append([
                Paragraph(str(ex['num']), self.meta_style),
                Paragraph(ex['exercise'], self.meta_style),
                Paragraph(str(ex['sets']), self.meta_style),
                Paragraph(ex['reps'], self.meta_style),
                Paragraph(ex['weight'], self.meta_style),
                Paragraph(ex['rest'], self.meta_style),
            ])

        table = Table(data, colWidths=[6*mm, 38*mm, 9*mm, 14*mm, 14*mm, 14*mm])
        table.setStyle(self._get_workout_table_style())
        return table

    def _get_workout_table_style(self) -> TableStyle:
        """Get reusable workout table styling."""
        return TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), FONT_SIZE_META),
            ('TOPPADDING', (0, 0), (-1, 0), PADDING_NORMAL),
            ('BOTTOMPADDING', (0, 0), (-1, 0), PADDING_NORMAL),
            # Body rows
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), FONT_SIZE_TABLE),
            ('TOPPADDING', (0, 1), (-1, -1), PADDING_NORMAL),
            ('BOTTOMPADDING', (0, 1), (-1, -1), PADDING_NORMAL),
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COLOR_ROW_ALT]),
            # Borders
            ('GRID', (0, 0), (-1, -1), BORDER_WIDTH_NORMAL, COLOR_BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), BORDER_WIDTH_HEADER, COLOR_HEADER_BORDER),
        ])

    def create_notes_section(self) -> Table:
        """Create a notes section with blank lined rows."""
        data = [
            [Paragraph('<b>Notes:</b>', self.meta_style)],
            *[[''] for _ in range(NOTES_ROW_COUNT)],
        ]

        table = Table(data, colWidths=[CARD_WIDTH])
        table.setStyle(self._get_notes_table_style())
        return table

    def _get_notes_table_style(self) -> TableStyle:
        """Get reusable notes table styling."""
        last_note_row = NOTES_ROW_COUNT
        return TableStyle([
            # Header row
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, 0), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, 0), FONT_SIZE_META),
            ('TOPPADDING', (0, 0), (-1, 0), PADDING_SMALL),
            ('BOTTOMPADDING', (0, 0), (-1, 0), PADDING_SMALL),
            # Blank note rows
            ('ALIGN', (0, 1), (-1, last_note_row), 'LEFT'),
            ('VALIGN', (0, 1), (-1, last_note_row), 'TOP'),
            ('HEIGHT', (0, 1), (-1, last_note_row), NOTES_ROW_HEIGHT),
            ('TOPPADDING', (0, 1), (-1, last_note_row), PADDING_SMALL),
            ('BOTTOMPADDING', (0, 1), (-1, last_note_row), PADDING_SMALL),
            # Only line at bottom of each note row
            ('LINEBELOW', (0, 1), (-1, last_note_row), BORDER_WIDTH_NORMAL, COLOR_DIVIDER),
        ])

    def create_day_section(self, day_num: int, day_name: str, day_data: dict) -> Table:
        """Create a day section: header, skill, exercise table, and notes."""
        elements = [Paragraph(day_name, self.day_style)]

        if 'skill' in day_data:
            elements.append(Paragraph(f"<i>Skill: {day_data['skill']}</i>", self.meta_style))
            elements.append(Spacer(1, SKILL_SPACER))

        elements.append(self.create_workout_table(day_data))
        elements.append(Spacer(1, TABLE_SPACER))
        elements.append(self.create_notes_section())

        container = Table([[e] for e in elements], colWidths=[CARD_WIDTH])
        container.setStyle(self._get_container_table_style())
        return container

    def _get_container_table_style(self) -> TableStyle:
        """Get reusable container table styling (no padding, top-left alignment)."""
        return TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ])

    def create_cutting_guide(self) -> Paragraph:
        """Create a dotted cutting line separator."""
        dots = "– " * 70
        return Paragraph(
            f"<font size={FONT_SIZE_CUT_LINE} color='#aaaaaa'>{dots}</font>",
            self.meta_style
        )

    def _get_grid_layout_style(self) -> TableStyle:
        """Get reusable 2-column grid styling."""
        return TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBETWEEN', (0, 0), (0, -1), BORDER_WIDTH_NORMAL, COLOR_DIVIDER),
        ])

    def _add_grid_row(self, story: list, left_section: Table, right_section: Table) -> None:
        """Add a 2-column grid row to the story."""
        grid = Table([[left_section, right_section]], colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH])
        grid.setStyle(self._get_grid_layout_style())
        story.append(grid)

    def build_pdf(self, week_data: dict, week_num: int, is_deload: bool = False) -> None:
        """Generate single-page PDF with 4 workout cards in 2x2 grid."""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
            leftMargin=PAGE_MARGIN,
            rightMargin=PAGE_MARGIN,
            topMargin=PAGE_MARGIN,
            bottomMargin=PAGE_MARGIN,
        )

        title = f"Week {week_num} — Upper/Lower Split{'  ⚠ DELOAD WEEK' if is_deload else ''}"
        story = []
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 1*mm))

        # Row 1: Monday | Wednesday
        self._add_grid_row(
            story,
            self.create_day_section(1, 'MON – Upper A', week_data['monday']),
            self.create_day_section(2, 'WED – Lower A', week_data['wednesday']),
        )
        story.append(Spacer(1, 0.5*mm))
        story.append(self.create_cutting_guide())
        story.append(Spacer(1, 0.5*mm))

        # Row 2: Friday | Saturday
        self._add_grid_row(
            story,
            self.create_day_section(3, 'FRI – Upper B', week_data['friday']),
            self.create_day_section(4, 'SAT – Lower B', week_data['saturday']),
        )

        doc.build(story)
        print(f"✅ PDF generated: {self.output_path}")

    @staticmethod
    def _get_workout_data() -> dict:
        """Get week 1 workout data."""
        return {
            'monday': {
                'skill': 'Chest-to-Wall Handstand (30 sec)',
                'exercises': [
                    {'num': '1', 'exercise': 'Bench Press', 'sets': '3', 'reps': '6–8', 'weight': '70 kg', 'rest': '3 min'},
                    {'num': '2', 'exercise': 'Incline DB Press', 'sets': '3', 'reps': '10', 'weight': '22.5 kg/DB', 'rest': '3 min'},
                    {'num': '3', 'exercise': 'Weighted Pull-ups', 'sets': '4', 'reps': '6–8', 'weight': 'BW + 5 kg', 'rest': '2.5 min'},
                    {'num': '4', 'exercise': 'Single-Arm DB Row', 'sets': '3', 'reps': '8–10', 'weight': '22.5 kg', 'rest': '2 min'},
                    {'num': '5', 'exercise': 'Lateral Raise', 'sets': '3', 'reps': '15', 'weight': '5 kg', 'rest': '60 sec'},
                    {'num': '6', 'exercise': 'DB Curl', 'sets': '3', 'reps': '10', 'weight': '10 kg', 'rest': '90 sec'},
                ],
            },
            'wednesday': {
                'skill': 'Pike Push-Up Progression (incline 45°, 8 reps)',
                'exercises': [
                    {'num': '1', 'exercise': 'Barbell Squat', 'sets': '4', 'reps': '5–6', 'weight': '90 kg', 'rest': '3 min'},
                    {'num': '2', 'exercise': 'Leg Press', 'sets': '3', 'reps': '10–12', 'weight': 'start moderate', 'rest': '2 min'},
                    {'num': '3', 'exercise': 'Romanian Deadlift', 'sets': '3', 'reps': '10', 'weight': '75 kg', 'rest': '2.5 min'},
                    {'num': '4', 'exercise': 'Leg Curl', 'sets': '3', 'reps': '10–12', 'weight': 'start moderate', 'rest': '90 sec'},
                    {'num': '5', 'exercise': 'Hanging Leg Raise', 'sets': '3', 'reps': '10', 'weight': 'BW', 'rest': '90 sec'},
                    {'num': '6', 'exercise': 'Calf Raise', 'sets': '3', 'reps': '15', 'weight': '36 kg', 'rest': '60 sec'},
                ],
            },
            'friday': {
                'skill': 'Muscle-Up Progression (jumping assist, 5 reps)',
                'exercises': [
                    {'num': '1', 'exercise': 'DB Shoulder Press', 'sets': '3', 'reps': '8–10', 'weight': '12.5 kg/DB', 'rest': '2.5 min'},
                    {'num': '2', 'exercise': 'Machine Chest Press', 'sets': '3', 'reps': '8–10', 'weight': 'start moderate', 'rest': '2 min'},
                    {'num': '3', 'exercise': 'Weighted Chin-ups', 'sets': '4', 'reps': '6–8', 'weight': 'BW + 5 kg', 'rest': '2.5 min'},
                    {'num': '4', 'exercise': 'Lat Pulldown', 'sets': '3', 'reps': '10–12', 'weight': 'start moderate', 'rest': '2 min'},
                    {'num': '5', 'exercise': 'Cable Fly (limited ROM)', 'sets': '3', 'reps': '12', 'weight': '10 kg/side', 'rest': '90 sec'},
                    {'num': '6', 'exercise': 'Face Pull', 'sets': '3', 'reps': '15', 'weight': '15 kg', 'rest': '60 sec'},
                ],
            },
            'saturday': {
                'skill': 'Chest-to-Wall Handstand (45 sec)',
                'exercises': [
                    {'num': '1', 'exercise': 'Deadlift', 'sets': '3', 'reps': '4–5', 'weight': '115 kg', 'rest': '3+ min'},
                    {'num': '2', 'exercise': 'Hack Squat', 'sets': '3', 'reps': '8–10', 'weight': 'start moderate', 'rest': '2 min'},
                    {'num': '3', 'exercise': 'Weighted Chin-ups', 'sets': '3', 'reps': '6–8', 'weight': 'BW + 5 kg', 'rest': '2.5 min'},
                    {'num': '4', 'exercise': 'Back Extension', 'sets': '3', 'reps': '10–12', 'weight': 'start moderate', 'rest': '2 min'},
                    {'num': '5', 'exercise': 'Leg Extension', 'sets': '3', 'reps': '12–15', 'weight': 'start moderate', 'rest': '90 sec'},
                    {'num': '6', 'exercise': 'Weighted Plank', 'sets': '3', 'reps': '60 sec', 'weight': 'BW + 5 kg', 'rest': '60 sec'},
                ],
            },
        }


if __name__ == '__main__':
    import json
    from pathlib import Path
    _HERE = Path(__file__).resolve().parent
    progress_path = str(_HERE / 'progress_log.json')
    output_dir = _HERE / 'outputs'
    output_dir.mkdir(exist_ok=True)
    if os.path.exists(progress_path):
        with open(progress_path) as f:
            progress = json.load(f)
        week_num = progress['meta']['current_week']
        is_deload = progress['deload']['is_deload_week']
        output_path = str(output_dir / f'Workout_Plan_Week_{week_num}.pdf')
        # Build week_data from progress exercises
        day_skills = {
            'monday':    'Chest-to-Wall Handstand (30 sec)',
            'wednesday': 'Pike Push-Up Progression (incline 45°, 8 reps)',
            'friday':    'Muscle-Up Progression (jumping assist, 5 reps)',
            'saturday':  'Chest-to-Wall Handstand (45 sec)',
        }
        week_data = {}
        for day_key, exercises in progress['exercises'].items():
            week_data[day_key] = {
                'skill': day_skills[day_key],
                'exercises': [
                    {'num': ex['num'], 'exercise': ex['exercise'], 'sets': ex['sets'],
                     'reps': ex['reps'], 'weight': ex['weight'], 'rest': ex['rest']}
                    for ex in exercises
                ],
            }
    else:
        week_num = 1
        is_deload = False
        output_path = str(output_dir / 'Workout_Plan_Week_1.pdf')
        week_data = WorkoutPDFGenerator._get_workout_data()

    generator = WorkoutPDFGenerator(output_path)
    generator.build_pdf(week_data=week_data, week_num=week_num, is_deload=is_deload)

    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024
        print(f"PDF generated: {output_path} ({file_size:.1f} KB)")
    else:
        print("PDF generation failed")
