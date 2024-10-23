from io import BytesIO
from random import randint
from PIL import ImageFont
from drawing.base import DrawingTemplate


class DefaultGuaranteeLetterTemplate(DrawingTemplate):

    class TextCoordinates:
        date = (120, 157)
        year = (200, 157)
        support_initials = (220, 210)
        client_initials = (380, 228)
        amount = (205, 246)
        site = (60, 246 + 18 + 18)

    def __init__(self, date: str, year: str, first_name: str, last_name: str, amount: str, site: str):
        super().__init__('assets/img/support/guarantee_letter_default.jpg')
        self.date = date
        self.year = year
        self.first_name = first_name
        self.last_name = last_name
        self.amount = amount
        self.site = site

        self.color = '#000000'

    def _generate(self) -> BytesIO:
        # self._image.convert('RGBA')
        font = ImageFont.truetype('assets/fonts/times.ttf', size=13)
        self._drawer.text(self.TextCoordinates.date, self.date, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.year, self.year, font=font, fill=self.color)

        font = ImageFont.truetype('assets/fonts/times.ttf', size=15)
        self._drawer.text(self.TextCoordinates.support_initials, self.first_name, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.client_initials, self.last_name, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.amount, self.amount, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.site, self.site, font=font, fill=self.color)

        buffer = BytesIO()
        self._image.save(buffer, format='JPEG')
        buffer.seek(0)

        return buffer


class CbGuaranteeLetterTemplate(DrawingTemplate):

    class TextCoordinates:
        date = (120, 238)
        year = (200, 238)
        name = (378, 326)
        amount = (570, 326)

    def __init__(self, date: str, year: str, name: str,  amount: str):
        super().__init__('assets/img/support/guarantee_letter_cb.jpg')
        self.date = date
        self.year = year
        self.name = name
        self.amount = amount

        self.color = (59, 59, 57)

    def _generate(self) -> BytesIO:
        font = ImageFont.truetype('assets/fonts/times.ttf', size=13)
        self._drawer.text(self.TextCoordinates.date, self.date, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.year, self.year, font=font, fill=self.color)

        font = ImageFont.truetype('assets/fonts/times.ttf', size=15)
        self._drawer.text(self.TextCoordinates.amount, self.amount, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.name, self.name, font=font.font_variant(size=14), fill=self.color)

        buffer = BytesIO()
        self._image.save(buffer, format='JPEG')
        buffer.seek(0)

        return buffer


class RefundStatusTemplate(DrawingTemplate):

    class TextCoordinates:
        date = (125, 124)
        name = (125, 92)
        reason = (125, 192)
        operation_num = (125, 20)

    def __init__(self, date: str, name: str, reason: str):
        super().__init__('assets/img/support/refund_status.jpg')
        self.date = date
        self.name = name
        self.reason = reason

        self.color = '#000000'

    def _generate(self) -> BytesIO:
        font = ImageFont.truetype('assets/fonts/times.ttf', size=13)
        self._drawer.text(self.TextCoordinates.operation_num, str(randint(111111, 999999)), font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.date, self.date, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.name, self.name, font=font, fill=self.color)
        self._drawer.text(self.TextCoordinates.reason, self.reason, font=font, fill=self.color)

        buffer = BytesIO()
        self._image.save(buffer, format='JPEG')
        buffer.seek(0)

        return buffer
