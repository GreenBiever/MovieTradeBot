from io import BytesIO
from typing import Any

from PIL import ImageFont, Image
from PIL.ImageDraw import ImageDraw
from drawing.base import MultipleImageDrawingTemplate, Coordinates2D, DrawingTemplate


class SupportMessageWithoutHashtagTemplate(MultipleImageDrawingTemplate):

    class TextCoordinates:
        class FirstScreenShot:
            time = Coordinates2D(80, 32)
            amount = Coordinates2D(490, 1306)
            website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

        class SecondScreenShot(FirstScreenShot):
            amount = Coordinates2D(490, 780)

    def __init__(self, time: str, amount: str, website_domain: str):
        self.time = time
        self.amount = amount
        self.website_domain = website_domain

    def _init_images(self):
        self._first_screenshot = Image.open('assets/img/support_worker/without_hashtag_1.png')
        self._second_screenshot = Image.open('assets/img/support_worker/without_hashtag_2.png')
        self._lock_icon = Image.open('assets/img/icons/lock.png')

    def _init_drawers(self):
        self._first_screenshot_drawer = ImageDraw(self._first_screenshot)
        self._second_screenshot_drawer = ImageDraw(self._second_screenshot)

    def _init_fonts(self):
        self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
        self._font_cario_regular = ImageFont.truetype('assets/fonts/Cairo-Regular.ttf')
        self._font_cario_semibold = ImageFont.truetype('assets/fonts/Cairo-SemiBold.ttf')

    def _get_drawable_items(self) -> list[tuple[Image.Image, ImageDraw, Any]]:
        return list(zip(
            [self._first_screenshot, self._second_screenshot],
            [self._first_screenshot_drawer, self._second_screenshot_drawer],
            [self.TextCoordinates.FirstScreenShot, self.TextCoordinates.SecondScreenShot]
        ))

    def _generate(self) -> list[BytesIO]:
        image_buffers: list[BytesIO] = []
        drawable_items = self._get_drawable_items()
        for screenshot, screenshot_drawer, text_coordinates in drawable_items:
            screenshot_drawer.text(
                text_coordinates.time, self.time,
                font=self._font_iphone_time.font_variant(size=45),
                fill='#000000'
            )
            screenshot_drawer.text(
                text_coordinates.amount, self.amount,
                font=self._font_cario_regular.font_variant(size=44),
                fill='#081229'
            )
            ws_domain_x_coord = text_coordinates.website_domain.x(self.website_domain)
            screenshot_drawer.text(
                (
                    ws_domain_x_coord,
                    text_coordinates.website_domain.y
                ),
                self.website_domain,
                font=self._font_cario_regular.font_variant(size=42),
                fill='#121312'
            )
            screenshot.paste(self._lock_icon, (ws_domain_x_coord - 60, 2190), self._lock_icon)

            image_buffer = BytesIO()
            screenshot.save(image_buffer, format='PNG')
            image_buffer.seek(0)
            image_buffers.append(image_buffer)

        return image_buffers


class SupportMessageWithRedundantHashtagTemplate(SupportMessageWithoutHashtagTemplate):

    class TextCoordinates:
        class FirstScreenShot:
            time = Coordinates2D(80, 32)
            amount = Coordinates2D(490, 1515)
            website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

        class SecondScreenShot(FirstScreenShot):
            amount = Coordinates2D(490, 650)

    def _init_images(self):
        self._first_screenshot = Image.open('assets/img/support_worker/with_hashtag_1.png')
        self._second_screenshot = Image.open('assets/img/support_worker/with_hashtag_2.png')
        self._lock_icon = Image.open('assets/img/icons/lock.png')


class SupportWithoutOrderNumberTemplate(DrawingTemplate):

    class TextCoordinates:
        time = Coordinates2D(80, 32)
        amount = Coordinates2D(490, 1105)
        website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

    def __init__(self, time: str, amount: str, website_domain: str):
        super().__init__('assets/img/support_worker/without_order_num.png')
        self.time = time
        self.amount = amount
        self.website_domain = website_domain

        self.color = (88, 90, 88)

    def _init_fonts(self):
        self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
        self._font_cario_regular = ImageFont.truetype('assets/fonts/Cairo-Regular.ttf')
        self._font_cario_semibold = ImageFont.truetype('assets/fonts/Cairo-SemiBold.ttf')

    def _init_assets(self):
        super()._init_assets()
        self._lock_icon = Image.open('assets/img/icons/lock.png')

    def _generate(self) -> BytesIO:
        self._drawer.text(
            self.TextCoordinates.time,
            self.time,
            font=self._font_iphone_time.font_variant(size=45),
            fill='#000000'
        )
        self._drawer.text(
            self.TextCoordinates.amount,
            self.amount,
            font=self._font_cario_regular.font_variant(size=44),
            fill='#081229'
        )

        ws_domain_x_coord = self.TextCoordinates.website_domain.x(self.website_domain)
        self._image.paste(self._lock_icon, (ws_domain_x_coord - 60, 2190), self._lock_icon)

        self._drawer.text(
            (
                ws_domain_x_coord,
                self.TextCoordinates.website_domain.y
            ),
            self.website_domain,
            font=self._font_cario_regular.font_variant(size=42),
            fill='#121312'
        )

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class SupportRefundTermsTemplate(MultipleImageDrawingTemplate):

    class TextCoordinates:
        class FirstScreenShot:
            time = Coordinates2D(80, 32)
            website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

        class SecondScreenShot(FirstScreenShot):
            amount = Coordinates2D(490, 780)

    def __init__(self, time: str, website_domain: str):
        self.time = time
        self.website_domain = website_domain

    def _init_images(self):
        self._first_screenshot = Image.open('assets/img/support_worker/refund_terms_1.png')
        self._second_screenshot = Image.open('assets/img/support_worker/refund_terms_2.png')
        self._lock_icon = Image.open('assets/img/icons/lock.png')

    def _init_drawers(self):
        self._first_screenshot_drawer = ImageDraw(self._first_screenshot)
        self._second_screenshot_drawer = ImageDraw(self._second_screenshot)

    def _init_fonts(self):
        self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
        self._font_cario_regular = ImageFont.truetype('assets/fonts/Cairo-Regular.ttf')
        self._font_cario_semibold = ImageFont.truetype('assets/fonts/Cairo-SemiBold.ttf')

    def _generate(self) -> list[BytesIO]:
        image_buffers: list[BytesIO] = []
        screenshots_with_drawers = zip(
            [self._first_screenshot, self._second_screenshot],
            [self._first_screenshot_drawer, self._second_screenshot_drawer],
            [self.TextCoordinates.FirstScreenShot, self.TextCoordinates.SecondScreenShot]
        )

        for screenshot, screenshot_drawer, text_coordinates in screenshots_with_drawers:
            screenshot_drawer.text(
                text_coordinates.time, self.time,
                font=self._font_iphone_time.font_variant(size=45),
                fill='#000000'
            )
            ws_domain_x_coord = text_coordinates.website_domain.x(self.website_domain)
            screenshot_drawer.text(
                (
                    ws_domain_x_coord,
                    text_coordinates.website_domain.y
                ),
                self.website_domain,
                font=self._font_cario_regular.font_variant(size=42),
                fill='#121312'
            )
            screenshot.paste(self._lock_icon, (ws_domain_x_coord - 60, 2190), self._lock_icon)

            image_buffer = BytesIO()
            screenshot.save(image_buffer, format='PNG')
            image_buffer.seek(0)
            image_buffers.append(image_buffer)

        return image_buffers
