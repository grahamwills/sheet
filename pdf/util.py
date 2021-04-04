import io
import importlib.resources
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, Table

import pdf.components


def readable(s: str):
    return s \
        .replace('-Regular', '') \
        .replace('-BoldOblique', ' \u2022 Bold Italic') \
        .replace('-BoldItalic', ' \u2022 Bold Italic') \
        .replace('-Oblique', ' \u2022 Italic') \
        .replace('-Italic', ' \u2022 Italic') \
        .replace('-Bold', ' \u2022 Bold') \
        .replace('Times-Roman', 'Times')


def build_font_choices():
    user_fonts = []
    install_font('Droid', 'DroidSerif', user_fonts)
    install_font('Parisienne', 'Parisienne', user_fonts)
    install_font('Post No Bills', 'PostNoBills', user_fonts)
    install_font('Roboto', 'Roboto', user_fonts)
    install_font('Western', 'Carnevalee Freakshow', user_fonts)
    install_font('Love You', 'I Love What You Do', user_fonts)
    install_font('Typewriter', 'SpecialElite', user_fonts)
    install_font('Star Jedi', 'Starjedi', user_fonts)
    install_font('28 Days Later', '28 Days Later', user_fonts)
    install_font('Caviar Dreams', 'CaviarDreams', user_fonts)
    install_font('Motion Picture', 'MotionPicture', user_fonts)
    install_font('Adventure', 'Adventure', user_fonts)
    install_font('Mrs. Monster', 'mrsmonster', user_fonts)
    return [(s, readable(s)) for s in sorted(base_fonts() + user_fonts)]


def base_fonts():
    cv = canvas.Canvas(io.BytesIO())
    fonts = cv.getAvailableFonts()
    fonts.remove('ZapfDingbats')
    fonts.remove('Symbol')
    return fonts


def create_single_font(name, resource_name, default_font_name, user_fonts):
    loc = importlib.resources.files('pdf').joinpath('resources').joinpath(resource_name + ".ttf")
    if loc.exists():
        pdfmetrics.registerFont(TTFont(name, loc))
        user_fonts.append(name)
        return name
    else:
        return default_font_name


def install_font(name, resource_name, user_fonts):
    try:
        pdfmetrics.getFont(name)
    except:
        regular = create_single_font(name, resource_name + "-Regular", None, user_fonts)
        bold = create_single_font(name + "-Bold", resource_name + "-Bold", regular, user_fonts)
        italic = create_single_font(name + "-Italic", resource_name + "-Italic", regular, user_fonts)
        bold_italic = create_single_font(name + "-BoldItalic", resource_name + "-BoldItalic", bold, user_fonts)
        pdfmetrics.registerFontFamily(name, normal=name, bold=bold, italic=italic, boldItalic=bold_italic)


def count_wrapped(flowable):
    if not flowable:
        return 0
    if isinstance(flowable, Paragraph):
        try:
            # We don't care if there are more than two lines
            return 1 if len(flowable.blPara.lines) > 1 else 0
        except:
            # No paragraphs means wrap failed badly
            return 1000
    if isinstance(flowable, Table):
        return sum([count_wrapped(cell) for cell in flowable.original_contents])
    if isinstance(flowable, pdf.components.TextField) or isinstance(flowable, Image):
        return 0
    if isinstance(flowable, pdf.components.Checkboxes):
        return 0 if flowable.fits_OK else 100
    raise Exception("Unexpected flowable content: " + str(flowable.__class__))


def try_wrap(table, width, diverge):
    w, h = table.wrap(width, 10000)
    n_wrapped = count_wrapped(table)
    return n_wrapped + h/100 + diverge * diverge / 1000
