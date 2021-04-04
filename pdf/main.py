import io
import json

from layout.models import Section
from util import try_wrap
from .util import build_font_choices
from .items import Part, build_document, build_inner_table, build_styles, build_outer_table


def extract_section(all, loc, styles):
    sections = [Part(d, styles) for d in all if d['location'] == loc]
    sections.sort(key=lambda s: s.order)
    return sections


def count_columns(sections):
    c1, c2, c3 = 0, 0, 0
    for s in sections:
        if s['location'] == Section.Location.COL1: c1 = 1
        if s['location'] == Section.Location.COL2: c2 = 1
        if s['location'] == Section.Location.COL3: c3 = 1
    return c1 + c2 + c3


def create_pdf(definition):
    build_font_choices()

    output = io.BytesIO()
    doc = build_document(definition['layout'], output)
    styles = build_styles(definition['styles'])
    sections = definition['sections']
    pad = definition['layout']['padding']

    n_columns = max(1, count_columns(sections))

    if n_columns == 1:
        main_table = build_content(pad, sections, styles, doc.width, [doc.width])
    if n_columns == 2:
        table_height = 9e99
        for s in [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]:
            colWidths = [doc.width * s, doc.width * (1 - s)]
            table = build_content(pad, sections, styles, doc.width, colWidths)
            table_h = try_wrap(table, doc.width, s - 0.5)
            if table_h < table_height:
                table_height = table_h
                main_table = table

    doc.build([main_table])
    return output.getvalue()


def build_content(pad, sections, styles, total_width, colWidths):
    top = extract_section(sections, Section.Location.TOP, styles)
    bottom = extract_section(sections, Section.Location.BOTTOM, styles)
    middle = list(filter(None, [
        extract_section(sections, Section.Location.COL1, styles),
        extract_section(sections, Section.Location.COL2, styles),
        extract_section(sections, Section.Location.COL3, styles),
    ]))

    mid_list = [build_inner_table(item, i == 0 or i < len(middle) - 1, pad, colWidths[i])
                for i, item in enumerate(middle)]

    main_table = build_outer_table(
            build_inner_table(top, False, pad, total_width),
            mid_list,
            build_inner_table(bottom, False, pad, total_width),
            pad, colWidths
    )
    return main_table


def create_txt(definition):
    return json.dumps(definition, indent=4)
