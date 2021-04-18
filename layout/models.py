from django.db import models


from pdf.util import build_font_choices


# This is the basic unit of 'ownership'; everything else belongs to one
class Layout(models.Model):
    name = models.CharField(max_length=100, unique=True)
    system = models.BooleanField(verbose_name="System Owned", default=False)
    unlock_key = models.CharField(max_length=100)
    width = models.FloatField(default=8.5, verbose_name='Page Width')
    height = models.FloatField(default=11, verbose_name='Page Height')
    margin = models.FloatField(default=0.5, verbose_name='Outer Margin')
    padding = models.FloatField(default=6, verbose_name='Section Spacing')

    def __str__(self):
        return "%s (%1.1fx%1.1fin)s" % (self.name, self.width, self.height)


# Text Style
class TextStyle(models.Model):
    class Name(models.TextChoices):
        NORMAL = 'norm', 'Normal'
        TITLE = 'ti', 'Title'
        SUBTITLE = 'sub', 'Subtitle'
        KEY = 'key', 'Key'
        MONOSPACED = 'mono', 'Monospaced'
        QUOTE = 'qt', 'Quote'
        STRONG = 'bold', 'Strong'
        CUSTOM_1 = 'cu1', 'Custom1'
        CUSTOM_2 = 'cu2', 'Custom2'
        CUSTOM_3 = 'cu3', 'Custom3'
        CUSTOM_4 = 'cu4', 'Custom4'
        CUSTOM_5 = 'cu5', 'Custom5'
        CUSTOM_6 = 'cu6', 'Custom6'
        CUSTOM_7 = 'cu7', 'Custom7'
        CUSTOM_8 = 'cu8', 'Custom8'
        CUSTOM_9 = 'cu9', 'Custom9'

    class Alignment(models.TextChoices):
        LEFT = 'L', 'Left'
        CENTER = 'C', 'Center'
        RIGHT = 'R', 'Right'
        JUSTIFY = 'J', 'Justify'

    owner = models.ForeignKey(Layout, on_delete=models.CASCADE)
    name = models.CharField('style name', max_length=4, choices=Name.choices, default=Name.NORMAL)
    font = models.CharField('font family', max_length=64, default='Helvetica', choices=build_font_choices())
    size = models.PositiveSmallIntegerField('text size', default=11)
    color = models.CharField('color', max_length=20, default='black')
    align = models.CharField('alignment', max_length=1, choices=Alignment.choices, default=Alignment.LEFT)
    suffix = models.CharField('suffix', max_length=4, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='Style name must be unique for each layout')
        ]

    def __str__(self):
        return "%s.%s" % (self.owner.name, TextStyle.Name(self.name).label)


# Define the style of a section
class Section(models.Model):
    class Location(models.TextChoices):
        TOP = 'T', 'Top'
        COL1 = '1', 'Column 1'
        COL2 = '2', 'Column 2'
        COL3 = '3', 'Column 3'
        BOTTOM = 'B', 'Bottom'

    owner = models.ForeignKey(Layout, on_delete=models.CASCADE)
    title = models.CharField(verbose_name='name', max_length=20, null=True, blank=True)
    location = models.CharField('location', max_length=2, choices=Location.choices, default=Location.TOP)
    order = models.IntegerField(verbose_name='order', default=1)
    columns = models.IntegerField(verbose_name='columns', choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=1)
    fill_color = models.CharField(verbose_name='background color', max_length=20, null=True, blank=True)
    border_color = models.CharField(verbose_name='border color', max_length=20, null=True, blank=True)
    text_style = models.CharField(verbose_name='text style', max_length=4, choices=TextStyle.Name.choices,
                                  default=TextStyle.Name.NORMAL)
    key_style = models.CharField(verbose_name='key style', max_length=4, choices=TextStyle.Name.choices,
                                 default=TextStyle.Name.KEY)
    line_spacing = models.FloatField(default=2, verbose_name='Internal Spacing')
    content = models.TextField(verbose_name='content', max_length=20000, null=True, blank=True)
    image = models.ImageField(verbose_name='image', upload_to='section_image/', null=True, blank=True)

    def content_trimmed(self, max_len=40):
        string = str(self.content).replace('[\n \t\r]+', ' ')
        if len(string) > max_len:
            string = string[:(max_len - 1)] + "\u2026"
        return string

    def __str__(self):
        return "%s \u00A7 %s" % (self.owner.name, self.title)

def add_layout(name, unlock_key, base_name):
    layout = Layout(name=name, unlock_key=unlock_key)
    layout.save()

    try:
        base = Layout.objects.get(name=base_name)

        # Copy styles
        for s in TextStyle.objects.filter(owner=base):
            print('before', s)
            s.owner = layout
            s.pk = None
            print('after', s)
            s.save()
        # Copy sections
        for s in Section.objects.filter(owner=base):
            print('before', s)
            s.owner = layout
            s.pk = None
            print('after', s)
            s.save()
    except:
        pass


