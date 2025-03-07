from PIL import Image, ImageDraw, ImageFont

_drawing_board = None

class DrawingBoard:
    def __init__(self, image: Image):
        self.image = image
        self.canvas = ImageDraw.Draw(image)
        self.font = ImageFont.load_default(30)

    def set_font_size(self, new_size):
        self.font = ImageFont.load_default(new_size)

    def add_verticle_line(self, left, top, height, color="green", line_width=2):
        self.canvas.line([(left, top), (left, top + height)], fill=color, width=line_width)

    def add_horizontal_line(self, left, top, width, color="green", line_width=2):
        self.canvas.line([(left, top), (left + width, top)], fill=color, width=line_width)

    def add_text(self, left, top, text, color="red"):
        self.canvas.text((left, top), text, fill=color, font=self.font)

    def add_rounded_rectangle(self, left, top, width, height, outline_color="yellow", border_width=2, radius=5):
        self.canvas.rounded_rectangle(
            [(left, top), (left+width, top+height)], 
            radius, 
            fill=None, 
            outline=outline_color, 
            width=border_width
        )

    @property
    def width(self):
        return self.image.width

    @property
    def height(self):
        return self.image.height

def get_current_drawing_board() -> DrawingBoard:
    assert _drawing_board is not None
    return _drawing_board  

def set_current_drawing_board(db: DrawingBoard):
    global _drawing_board
    _drawing_board = db


