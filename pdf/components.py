from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Image, Table, TableStyle


class TitledTable(Table):
    title_size = 7
    title_font = 'Helvetica-Bold'

    def __init__(self, data, style_commands, base_style=None, title=None, title_on_left=True, box_stroke=None,
                 box_fill=None,
                 colWidths=None):
        self.original_contents = [cell for row in data for cell in row]
        if base_style:
            self.title_on_left = title_on_left
            self.title = title
            if title_on_left:
                style_commands.append(('LEFTPADDING', (0, 0), (0, -1), self.title_size/2))
            else:
                style_commands.append(('RIGHTPADDING', (-1, 0), (-1, -1), self.title_size/2))
        else:
            self.title = None

        super().__init__(data, style=TableStyle(style_commands), colWidths=colWidths)
        self.box_fill = box_fill
        self.box_stroke = box_stroke

    def draw(self):
        canvas = self.canv
        canvas.saveState()

        canvas.setLineWidth(0.5)
        W = self._width
        H = self._height
        if self.box_stroke: canvas.setStrokeColor(self.box_stroke)
        if self.box_fill: canvas.setFillColor(self.box_fill)

        if self.title:
            E = self.title_size / 2
            fsize = self.title_size
            L = stringWidth(self.title, 'Helvetica-Bold', fsize) + fsize / 2

            if L > H - 2 * E:
                fsize *= (H - 2 * E) / L
                L = H - 2 * E

            if not self.title_on_left:
                canvas.translate(W / 2, H / 2)
                canvas.rotate(180)
                canvas.translate(-W / 2, -H / 2)

            p = canvas.beginPath()
            p.moveTo(0, (H - L) / 2)
            p.arcTo(0, 2 * E, 3 * E, 0, startAng=180)
            p.lineTo(W, 0)
            p.lineTo(W, H)
            p.lineTo(2 * E, H)
            p.arcTo(0, H - 2 * E, 3 * E, H, startAng=90)
            p.lineTo(0, (H + L) / 2)
            canvas.drawPath(p, fill=bool(self.box_fill))

            canvas.setFont(self.title_font, fsize)
            canvas.translate(fsize * 4 / 5 - E, H / 2)
            canvas.rotate(90)
            canvas.setFillColor(self.box_stroke)
            canvas.drawCentredString(0, 0, self.title)
        else:
            canvas.rect(0, 0, W, H, fill=bool(self.box_fill), stroke=bool(self.box_stroke))

        canvas.restoreState()

        super().draw()
        canvas.saveState()
        canvas.restoreState()


class Checkboxes(Flowable):
    def __init__(self, boxes, line_height):
        super().__init__()
        self.size = line_height
        self.pad = 6
        self.boxes = boxes
        self.count = len(boxes)

    def wrap(self, availWidth, availHeight):
        wid = self.size * self.count + self.pad * (self.count - 1)
        self.fits_OK = wid < availWidth
        return (wid, self.size)

    def draw(self):
        canvas = self.canv
        form = canvas.acroForm
        D = self.size
        P = self.pad
        F = self.size / 2 + 1
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', F)
        canvas.setLineWidth(0.5)
        for type in self.boxes:
            normal = type == 'X' or type == 'O'
            if normal:
                col = colors.navy
            else:
                col = colors.red
            form.checkbox(x=2, y=-1, buttonStyle='cross', relative=True, size=D,
                          textColor=col, fillColor=colors.transparent, borderColor=colors.transparent,
                          borderWidth=0, checked=(type == 'X'))
            if not normal:
                p = canvas.beginPath()
                p.moveTo(0.5, D / 2 - F / 4 - 1)
                p.lineTo(0.5, -2)
                p.lineTo(D + 3, -2)
                p.lineTo(D + 3, D)
                p.lineTo(0.5, D)
                p.lineTo(0.5, D - F / 4)
                canvas.drawPath(p)
                canvas.drawString(0.5 - F / 4, D - F - 0.5, type)
            else:
                canvas.rect(0.5, -2, D + 3, D + 2)
            canvas.translate(D + P, 0)

        canvas.restoreState()


class TextField(Flowable):
    def __init__(self, style):
        super().__init__()
        self.style = style

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return (availWidth, self.style.fontSize + 4)

    def draw(self):
        c = self.canv
        form = c.acroForm
        style = self.style
        form.textfield(x=- 2, y=- 1, relative=True, width=self.width + 1, height=style.fontSize + 3,
                       fontName='Helvetica', fontSize=style.fontSize, textColor=style.textColor,
                       fillColor=HexColor(0xF4F4FF), borderWidth=0.5, borderColor=colors.lightgrey)


class ImageAutoSize(Image):
    def __init__(self, image, width):
        super().__init__(image, lazy=0)
        resize = min(1, width / image.width)
        self.drawWidth = self.imageWidth * resize
        self.drawHeight = self.imageHeight * resize