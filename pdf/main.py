import io
import json

from reportlab.platypus import Paragraph, Table

import pdf.components
from layout.models import Section
from .util import build_font_choices
from .items import Part, build_document, build_inner_table, build_styles, build_outer_table


def extract_section(all, loc, styles):
    sections = [Part(d, styles) for d in all if d['location'] == loc]
    sections.sort(key=lambda s: s.order)
    return sections


def count_wrapped(flowable):
    if not flowable:
        return 0
    if isinstance(flowable, Paragraph):
        # We don't care if there are more than two lines
        return 1 if len(flowable.blPara.lines) > 1 else 0
    if isinstance(flowable, Table):
        return sum([count_wrapped(cell) for cell in flowable.original_contents])
    if isinstance(flowable, pdf.components.TextField):
        return 0
    if isinstance(flowable, pdf.components.Checkboxes):
        return 0 if flowable.fits_OK else 1000
    raise Exception("Unexpected flowable content: " + str(flowable.__class__))


def try_wrap(table, width, diverge):
    w, h = table.wrap(width, 10000)
    n_wrapped = count_wrapped(table)
    return 20 * n_wrapped + h + 10 * diverge * diverge


def create_pdf(definition):
    build_font_choices()

    output = io.BytesIO()
    doc = build_document(definition['layout'], output)
    styles = build_styles(definition['styles'])
    sections = definition['sections']
    pad = definition['layout']['padding']

    main_table, n_columns = build_content(pad, sections, styles)

    if n_columns == 2:
        table_height = try_wrap(main_table, doc.width, 0)
        for s in [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]:
            colWidths = [doc.width * s, doc.width * (1 - s)]
            table, n_columns = build_content(pad, sections, styles, colWidths=colWidths)
            table_h = try_wrap(table, doc.width, s - 0.5)
            if table_h < table_height:
                table_height = table_h
                main_table = table

    doc.build([main_table])
    return output.getvalue()


def build_content(pad, sections, styles, colWidths=None):
    top = extract_section(sections, Section.Location.TOP, styles)
    bottom = extract_section(sections, Section.Location.BOTTOM, styles)
    middle = list(filter(None, [
        extract_section(sections, Section.Location.COL1, styles),
        extract_section(sections, Section.Location.COL2, styles),
        extract_section(sections, Section.Location.COL3, styles),
    ]))
    right_item = middle[-1] if len(middle) > 1 else None
    main_table = build_outer_table(
            build_inner_table(top, False, pad),
            [build_inner_table(i, i != right_item, pad) for i in middle],
            build_inner_table(bottom, False, pad),
            pad, colWidths
    )
    return main_table, max(1, len(middle))


def create_txt(definition):
    return json.dumps(definition, indent=4)
