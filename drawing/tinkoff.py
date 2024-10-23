from io import BytesIO
from PIL import ImageFont, Image
from .base import DrawingTemplate, Coordinates2D


class TinkoffIncomePaymentTemplate(DrawingTemplate):

    class TextCoordinates:
        time = (72, 35)
        website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

    def __init__(self, time: str, amount: str, date: str, name: str, payment_type: str):
        super().__init__('assets/img/tinkoff/tinkoff_p_template.png')
        self.time = time
        self.date = date
        self.name = name
        self.amount = f'+ {amount} ₽'
        self.payment_type = payment_type

    def _init_fonts(self):
        self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
        self._font_iphone_other = ImageFont.truetype('assets/fonts/iphone_other.ttf')
        self._font_payment_font = ImageFont.truetype('assets/fonts/payment_font.ttf')

    def _init_assets(self):
        super()._init_assets()
        self._geo_icon = Image.open('assets/img/icons/geo_active.png')

    def _generate(self) -> BytesIO:
        self._drawer.text(self.TextCoordinates.time, self.time, font=self._font_iphone_time.font_variant(size=45))
        self._image.paste(self._geo_icon, (72+len(self.time)*29, 35), self._geo_icon)

        current_font = self._font_iphone_other.font_variant(size=45)
        w, h = self._drawer.textsize(self.name, font=current_font)
        self._drawer.text(((1170-w) / 2, 845), self.name, font=current_font)

        w, h = self._drawer.textsize(self.date, font=current_font)
        self._drawer.text(((1170-w) / 2, 423), self.date, font=current_font, fill="#343434")

        current_font = self._font_payment_font.font_variant(size=110)
        w, h = self._drawer.textsize(self.amount, font=current_font)
        self._drawer.text(((1170-w) / 2, 1030), self.amount, font=current_font, fill="#43b232")

        current_font = self._font_iphone_other.font_variant(size=45)
        self._drawer.text((52, 2111), self.name, font=current_font)

        w, h = self._drawer.textsize(self.payment_type, font=current_font)
        self._drawer.text(((1170-w) / 2, 923), self.payment_type, font=current_font, fill="#7b8187")

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer


class TinkoffOutgoingPaymentTemplate(DrawingTemplate):

    class TextCoordinates:
        time = (72,30)
        website_domain = Coordinates2D(lambda ws_domain: 560 - (len(ws_domain) - 1) * 10, 2178)

    def __init__(self, time: str, amount: str, current_cash: str, cc_num: str, name: str):
        super().__init__('assets/img/tinkoff/tinkoff_rec_template.png')
        self.time = time
        self.amount = amount
        self.current_cash = current_cash
        self.cc_num = cc_num
        self.name = name

    def _init_fonts(self):
        self._font_iphone_time = ImageFont.truetype('assets/fonts/iphone_time.ttf')
        self._font_iphone_other = ImageFont.truetype('assets/fonts/iphone_other.ttf')
        self._font_payment_font = ImageFont.truetype('assets/fonts/payment_font.ttf')
        self._font_credit_card = ImageFont.truetype('assets/fonts/cc_tinkoff.ttf')

    def _init_assets(self):
        super()._init_assets()
        self._geo_icon = Image.open('assets/img/icons/geo_active.png')

    def _generate(self) -> BytesIO:
        # ОТРИСОВКА ВРЕМЕНИ
        current_font = self._font_iphone_time.font_variant(size=45)
        self._drawer.text((72, 30), self.time, font=current_font)
        self._image.paste(self._geo_icon, (72+len(self.time)*29, 35), self._geo_icon)

        # ОТРИСОВКА СУММЫ ПЛАТЕЖА
        display_amount = f'- {self.amount} ₽'
        current_font = self._font_payment_font.font_variant(size=110)
        w, h = self._drawer.textsize(display_amount, font=current_font)
        self._drawer.text(((1170-w) / 2, 885), display_amount, font=current_font)

        # ВСТАВКА БАЛАНСА КАРТЫ
        current_font = self._font_iphone_other.font_variant(size=45)
        self._drawer.text((645, 775), str(int(int(self.current_cash) - int(self.amount))) + ' ₽', font=current_font)

        # ВСТАВКА ПРОШЛОГО БАЛАНСА КАРТЫ
        display_prev_cash = f'{self.current_cash} ₽'
        w, h = self._drawer.textsize(display_prev_cash, font=current_font)
        self._drawer.text(((527-w), 775), display_prev_cash, font=current_font)
        self._drawer.line(((527-w), 800, 530, 800), width=3)

        # ВСТАВКА НОМЕРА КАРТЫ
        current_font = self._font_credit_card.font_variant(size=45)
        cc_number = f"{self.cc_num[:6]}{'*'*6}{self.cc_num[-4:]}"
        w, h = self._drawer.textsize(cc_number, font=current_font)
        self._drawer.text(((1170-w) / 2, 1440), cc_number, font=current_font, fill="black")

        # ВСТАВКА ИМЕНИ
        current_font = self._font_iphone_other.font_variant(size=45)
        w, h = self._drawer.textsize(self.name, font=current_font)
        print(self.name)
        self._drawer.text(((1170-w) / 2, 1083), self.name, font=current_font, fill="#7b8187")

        buffer = BytesIO()
        self._image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer
