from io import BytesIO
from PIL import ImageFont, Image

from hosting.websites.all import PaymentSystem
from .base import DrawingTemplate, Coordinates2D


class PaymentSystemDrawingTemplate(DrawingTemplate):

    async def _load_autocomplete_values(self):
        self.website_domain = f'{await PaymentSystem.get_current_domain_name()}'

    def _init_fonts(self):
        self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
        self._font_cario_semibold = ImageFont.truetype('assets/fonts/Cairo-SemiBold.ttf')

    def _init_assets(self):
        super()._init_assets()
        self._lock_icon = Image.open('assets/img/icons/lock.png')


class PaymentSystemNoteTemplate(PaymentSystemDrawingTemplate):

    class TextCoordinates:
        time = (80, 30)
        website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

    def __init__(self, time: str):
        super().__init__('assets/img/payment_sys/note.png')
        self.time = time
        self.website_domain = None

    # def _init_fonts(self):
    #     self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
    #     self._font_cario_semibold = ImageFont.truetype('assets/fonts/Cairo-SemiBold.ttf')
    #
    # def _init_assets(self):
    #     super()._init_assets()
    #     self._lock_icon = Image.open('assets/img/icons/lock.png')

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45), fill='#000000')
        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._drawer.text(
            (ws_domain_x_coord, self.TextCoordinates.website_domain.y),
            self.website_domain,
            font=self._font_cario_semibold.font_variant(size=52),
            fill='#E5E5E5'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class PaymentSystemRefundSuccessTemplate(PaymentSystemDrawingTemplate):

    class TextCoordinates:
        time = (80, 30)
        website_domain = Coordinates2D(lambda ws_domain: 540 - (len(ws_domain) - 1) * 10, 2174)

    def __init__(self, time: str):
        super().__init__('assets/img/payment_sys/refund_success.png')
        self.time = time
        self.website_domain = None

    # def _init_fonts(self):
    #     self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
    #     self._font_cario_semibold = ImageFont.truetype('assets/fonts/Cairo-SemiBold.ttf')
    #
    # def _init_assets(self):
    #     super()._init_assets()
    #     self._lock_icon = Image.open('assets/img/icons/lock.png')

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45), fill='#000000')
        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._drawer.text(
            (ws_domain_x_coord, self.TextCoordinates.website_domain.y),
            self.website_domain,
            font=self._font_cario_semibold.font_variant(size=52),
            fill='#E5E5E5'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class PaymentSystemNonEquivalently(PaymentSystemDrawingTemplate):

    class TextCoordinates:
        time = (80, 30)
        website_domain = Coordinates2D(lambda ws_domain: 540 - (len(ws_domain) - 1) * 10, 2174)

    def __init__(self, time: str):
        super().__init__('assets/img/payment_sys/not_equivalently.png')
        self.time = time
        self.website_domain = None

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45), fill='#000000')
        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._drawer.text(
            (ws_domain_x_coord, self.TextCoordinates.website_domain.y),
            self.website_domain,
            font=self._font_cario_semibold.font_variant(size=52),
            fill='#E5E5E5'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class PaymentSystemTransactionRestricted(PaymentSystemDrawingTemplate):

    class TextCoordinates:
        time = (80, 30)
        website_domain = Coordinates2D(lambda ws_domain: 540 - (len(ws_domain) - 1) * 10, 2174)

    def __init__(self, time: str):
        super().__init__('assets/img/payment_sys/transaction_restricted.png')
        self.time = time
        self.website_domain = None

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45), fill='#000000')
        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._drawer.text(
            (ws_domain_x_coord, self.TextCoordinates.website_domain.y),
            self.website_domain,
            font=self._font_cario_semibold.font_variant(size=52),
            fill='#E5E5E5'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class PaymentSystemUnknownError(PaymentSystemDrawingTemplate):

    class TextCoordinates:
        time = (80, 30)
        website_domain = Coordinates2D(lambda ws_domain: 540 - (len(ws_domain) - 1) * 10, 2174)

    def __init__(self, time: str):
        super().__init__('assets/img/payment_sys/unknown_error.png')
        self.time = time
        self.website_domain = None

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45), fill='#000000')
        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._drawer.text(
            (ws_domain_x_coord, self.TextCoordinates.website_domain.y),
            self.website_domain,
            font=self._font_cario_semibold.font_variant(size=52),
            fill='#E5E5E5'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class PaymentSystemCardNotSupported(PaymentSystemDrawingTemplate):

    class TextCoordinates:
        time = (80, 30)
        website_domain = Coordinates2D(lambda ws_domain: 540 - (len(ws_domain) - 1) * 10, 2174)

    def __init__(self, time: str):
        super().__init__('assets/img/payment_sys/card_not_supported.png')
        self.time = time
        self.website_domain = None

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45), fill='#000000')
        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._drawer.text(
            (ws_domain_x_coord, self.TextCoordinates.website_domain.y),
            self.website_domain,
            font=self._font_cario_semibold.font_variant(size=52),
            fill='#E5E5E5'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class PaymentSystemIncorrectOrderNumber(PaymentSystemDrawingTemplate):

    class TextCoordinates:
        time = (80, 30)
        website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

    def __init__(self, time: str):
        super().__init__('assets/img/payment_sys/incorrect_order_number.png')
        self.time = time
        self.website_domain = None

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45), fill='#000000')
        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._drawer.text(
            (ws_domain_x_coord, self.TextCoordinates.website_domain.y),
            self.website_domain,
            font=self._font_cario_semibold.font_variant(size=52),
            fill='#E5E5E5'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer
