import re

from django.db.models import ImageField
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.colors import toColorOrNone, Color
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Table, TableStyle

from .components import Checkboxes, ImageAutoSize, TextField, TitledTable
from layout.models import TextStyle

DEBUG = 0


def asColor(param):
    return toColorOrNone(param)


def asAlignment(param):
    if param == TextStyle.Alignment.LEFT:
        return TA_LEFT
    if param == TextStyle.Alignment.RIGHT:
        return TA_RIGHT
    if param == TextStyle.Alignment.CENTER:
        return TA_CENTER
    if param == TextStyle.Alignment.JUSTIFY:
        return TA_JUSTIFY
    raise Exception('Unknown alignment')


def build_styles(items):
    styles = StyleSheet1()
    for item in items:
        sz = item['size']
        style = ParagraphStyle(
                name=item['name'],
                fontName=item['font'],
                fontSize=sz,
                textColor=asColor(item['color']),
                alignment=asAlignment(item['align']),
                allowOrphans=False,
                allowOWidows=False,
                leading=sz * 1.2
        )
        style.suffix = item['suffix']
        styles.add(style)
    return styles


def build_document(page, output):
    margin_inch = page['margin'] * inch
    return SimpleDocTemplate(output,
                             pagesize=[page['width'] * inch, page['height'] * inch],
                             rightMargin=margin_inch,
                             leftMargin=margin_inch,
                             topMargin=margin_inch,
                             bottomMargin=margin_inch)


def build_outer_table(top_flow, middle_flow, bottom_flow, padding, colWidths):
    data = []
    style_commands = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),

        ('LEFTPADDING', (1, 0), (-1, -1), padding),
        ('TOPPADDING', (0, 1), (-1, -1), padding),
    ]

    cols = max(1, len(middle_flow))
    row = 0

    # Add top section, ensuring span is good
    if top_flow:
        data.append([top_flow])
        if cols > 1:
            style_commands.append(('SPAN', (0, row), (-1, row)))
        row += 1

    # Add center sections
    if middle_flow:
        data.append(middle_flow)
        row += 1

    # Add bottom section, ensuring span is good
    if bottom_flow:
        data.append([bottom_flow])
        if cols > 1:
            style_commands.append(('SPAN', (0, row), (-1, row)))
        row += 1

    if DEBUG:
        style_commands.append(('BACKGROUND', (0, 0), (-1, -1), Color(0, 0, 1, 0.1)))
        style_commands.append(('GRID', (0, 0), (-1, -1), 1, Color(0, 0, 1, 0.25)))

    return make_table(data, style_commands, colWidths)


def make_table(data, style_commands, colWidths):
    table = Table(data, style=TableStyle(style_commands), colWidths=colWidths)
    table.original_contents = [cell for row in data for cell in row]
    return table


def build_inner_table(sections, on_left, padding, width):
    if not sections:
        return None

    data = [[s.as_flow(on_left, width)] for s in sections]
    style_commands = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 1), (-1, -1), padding)
    ]

    if DEBUG:
        style_commands.append(('BACKGROUND', (0, 0), (-1, -1), Color(0.5, 0.5, 0, 0.1)))
        style_commands.append(('GRID', (0, 0), (-1, -1), 1, Color(0.5, 0.5, 0, 0.5)))

    return make_table(data, style_commands, colWidths=None)


class Part():
    pair_matcher = re.compile(r'([^=]+)=([^=]+)')
    textfield_matcher = re.compile(r'^\[\s*]$')

    def __init__(self, definition, styles):
        self.title = definition['title']
        self.order = definition['order']
        self.columns = definition['columns']
        self.fill_color = asColor(definition['fill_color'])
        self.border_color = asColor(definition['border_color'])
        self.text_style = styles[definition['text_style']]
        self.key_style = styles[definition['key_style']]
        self.title_style = styles['bold']
        self.line_spacing = definition['line_spacing']
        self.location = definition['location']
        self.image = definition['image']
        self.content = [self.make_items(i) for i in definition['content'].splitlines()]
        self.is_pairs = self.content and len(max(self.content, key=len)) > 1

    def regularize(self, value):
        if len(value) == 1:
            return [None, value[0]]
        else:
            return value

    def as_flow(self, on_left, width):

        # Adjust for extra padding for title
        if self.title and self.border_color:
            width -= TitledTable.title_size / 2


        if self.image:
            style_commands = [
                ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]
            content = [[ImageAutoSize(self.image, width)]]
        else:
            style_commands = [
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), self.line_spacing),
                ('RIGHTPADDING', (0, 0), (-1, -1), self.line_spacing),
                ('TOPPADDING', (0, 0), (-1, -1), self.line_spacing),
                ('BOTTOMPADDING', (0, 0), (-1, -1), self.line_spacing),
            ]
            if self.is_pairs:
                content = []
                for item in self.content:
                    if len(item) == 1:
                        content.append(None)
                        content.append(item[0])
                    else:
                        content += item
            else:
                content = [c[0] for c in self.content]

            content = self.wrap(content, self.columns * (2 if self.is_pairs else 1))

        if not content:
            return Paragraph("", style=self.text_style)
        if self.border_color:
            return TitledTable(content, style_commands, self.title_style,
                               title=self.title, title_on_left=on_left, box_stroke=self.border_color,
                               box_fill=self.fill_color)
        else:
            return TitledTable(content, style_commands)

    def make_items(self, content):
        if DEBUG:
            style = ParagraphStyle('debug', borderColor=Color(1, 0, 0, 1), borderWidth=1,
                                   parent=self.text_style)
            key_style = ParagraphStyle('debug', borderColor=Color(1, 0, 0, 1), borderWidth=1,
                                       parent=self.key_style)
        else:
            style = self.text_style
            key_style = self.key_style

        txt = str(content).strip()
        match = Part.pair_matcher.match(txt)
        if match:
            key = self.remove_quote(match.group(1).strip())
            value = self.remove_quote(match.group(2).strip())
            return self.make_paragraphs(key, key_style) + self.make_paragraphs(value, style)
        else:
            return self.make_paragraphs(txt, style)

    def make_paragraphs(self, txt, style):

        boxes = self.parse_boxes(txt, style)
        if boxes:
            return boxes

        if Part.textfield_matcher.match(txt):
            return [TextField(style)]
        if style.suffix:
            txt += style.suffix
        return [Paragraph(txt, style=style)]

    def wrap(self, content, cols):
        result = []
        for i in range(0, len(content), cols):
            result.append(content[i:min(i + cols, len(content))])
        return result

    def remove_quote(self, txt):
        if txt and txt[0] == txt[-1] and (txt[0] == "'" or txt[0] == '"'):
            return txt[1:-1]
        else:
            return txt

    def parse_boxes(self, txt, style):
        txt = txt.replace(r'\s', '')
        result = []
        while len(txt) >= 3:
            if txt[0] == '[' and txt[2] == ']':
                result.append(txt[1])
            else:
                return None
            txt = txt[3:]
        if result and not txt:
            return [Checkboxes(result, style.fontSize * 0.9)]
        else:
            return None
