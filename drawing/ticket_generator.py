from io import BytesIO
from random import randint

from PIL import ImageFont
from drawing.base import DrawingTemplate


class TheatreTicket(DrawingTemplate):
    class TextCoordinates:
        event_name = (498, 328)
        price = (465, 257)
        seat = (413, 291)
        date = (395, 221)
        order_number = (152, 414)

    def __init__(self, event_name: str, price: str, seat: str, date: str):
        super().__init__('assets/img/theatre_ticket_template_new.png')
        self.event = event_name
        self.price = price
        self.seat = seat
        self.date = date
        self.order_number = None

    async def _load_autocomplete_values(self):
        self.order_number = str(randint(100_000_000_00, 999_999_999_99))

    def _init_fonts(self):
        self._font_default = ImageFont.truetype('assets/fonts/MyriadProRegular.otf', 13)
        self._font_roboto_light = ImageFont.truetype('assets/fonts/Robotolight.ttf', 20)

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.event_name, self.event, font=self._font_roboto_light,
                          fill=(254, 251, 247))
        self._drawer.text(self.TextCoordinates.price, f"{self.price} руб.", font=self._font_roboto_light,
                          fill=(254, 251, 247))
        self._drawer.text(self.TextCoordinates.seat, self.seat, font=self._font_roboto_light, fill=(254, 251, 247))
        self._drawer.text(self.TextCoordinates.date, self.date, font=self._font_roboto_light, fill=(254, 251, 247))
        self._drawer.text(self.TextCoordinates.order_number, self.order_number, font=self._font_default, fill=(0, 0, 0))

        buffer = BytesIO()
        self._image.save(buffer, format='JPEG')
        buffer.seek(0)

        return buffer


class CinemaTicket(DrawingTemplate):
    MAIN_FONT = ImageFont.truetype('assets/fonts/fontb.ttf', 18)

    class TextCoordinates:
        room_name = (446, 556)
        price = (463, 586)
        date = (410, 616)

    def __init__(self, room_name: str, price: str, date: str):
        super().__init__('assets/img/cinema_ticket_template.png')
        self.room_name = room_name
        self.price = price
        self.date = date

        self.color = (23, 21, 21)

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.room_name, self.room_name, font=self.MAIN_FONT, fill=self.color)
        self._drawer.text(self.TextCoordinates.price, f'{self.price} ₽', font=self.MAIN_FONT, fill=self.color)
        self._drawer.text(self.TextCoordinates.date, self.date, font=self.MAIN_FONT, fill=self.color)

        buffer = BytesIO()
        self._image.save(buffer, format='png')
        buffer.seek(0)

        return buffer


class ExhibitionTicket(DrawingTemplate):
    MAIN_FONT = ImageFont.truetype('assets/fonts/Roboto.ttf', 28)

    class TextCoordinates:
        event_name = (350, 688)
        price = (313, 808)
        date = (607, 806)

    def __init__(self, event_name: str, price: str, date: str, time: str):
        super().__init__('assets/img/exhibitions_ticket_template.png')
        self.event_name = event_name
        self.price = price
        self.date = date
        self.time = time

        self.color = (255, 255, 255)

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.event_name, self.event_name, font=self.MAIN_FONT, fill=self.color)
        self._drawer.text(self.TextCoordinates.price, f'{self.price} руб.', font=self.MAIN_FONT, fill=self.color)
        self._drawer.text(self.TextCoordinates.date, f'{self.date}, {self.time}', font=self.MAIN_FONT, fill=self.color)

        buffer = BytesIO()
        self._image.save(buffer, format='png')
        buffer.seek(0)

        return buffer


class StandupTicket(DrawingTemplate):
    MAIN_FONT = ImageFont.truetype('assets/fonts/Roboto.ttf', 28)

    class TextCoordinates:
        event_name = (364, 324)
        price = (321, 484)
        date = (224, 644)

    def __init__(self, event_name: str, price: str, date: str, time: str):
        super().__init__('assets/img/standup_ticket_template.png')
        self.event_name = event_name
        self.price = price
        self.date = date
        self.time = time

        self.color = (88, 90, 88)

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.event_name, self.event_name, font=self.MAIN_FONT, fill=self.color)
        self._drawer.text(self.TextCoordinates.price, f'{self.price} руб.', font=self.MAIN_FONT, fill=self.color)
        self._drawer.text(self.TextCoordinates.date, f'{self.date}, {self.time}', font=self.MAIN_FONT, fill=self.color)

        buffer = BytesIO()
        self._image.save(buffer, format='png')
        buffer.seek(0)

        return buffer
