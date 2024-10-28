import abc
import logging
from dataclasses import dataclass
from typing import Type
import io

from aiogram.fsm.state import StatesGroup, State

from app_dependency import dp as Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, \
    InputMediaPhoto, FSInputFile, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_toolbet.exceptions.menu import StopRender
from aiogram_toolbet.menu.base import DynamicMenu
from aiogram_toolbet.menu.meta import MenuHook
from aiogram_toolbet.menu.state_var import StateVar
from databases.models import DrawingCategoryAllowedUsers
from drawing.base import TicketTemplateT
from drawing.payment_system import PaymentSystemRefundSuccessTemplate, \
    PaymentSystemNonEquivalently, PaymentSystemTransactionRestricted, PaymentSystemUnknownError, \
    PaymentSystemCardNotSupported, PaymentSystemIncorrectOrderNumber
from drawing.support_scripts import DefaultGuaranteeLetterTemplate, CbGuaranteeLetterTemplate, RefundStatusTemplate
from drawing.ticket_generator import CinemaTicket, TheatreTicket, ExhibitionTicket, StandupTicket
from drawing.tinkoff import TinkoffIncomePaymentTemplate, TinkoffOutgoingPaymentTemplate
from drawing.worker_support import SupportMessageWithoutHashtagTemplate, SupportMessageWithRedundantHashtagTemplate, \
    SupportRefundTermsTemplate, SupportWithoutOrderNumberTemplate
from users.role.default import UserRoles
from users.role.role import UserRole
from users.user import User

WAITING_TICKET_DATA = "DrawWizard:WAITING_TICKET_DATA"


class TemplateState(StatesGroup):
    key = State()
    valute = State()


@dataclass
class DrawingTemplate:
    template_drawer_cls: Type[TicketTemplateT]
    description: str
    name: str
    preview_images: list[str] = None


class DrawingTemplateWithRestrictedAccess(DrawingTemplate):

    @abc.abstractmethod
    async def check_access(self, **context) -> bool:
        raise NotImplemented


@dataclass
class DrawingTemplateRestrictedByRole(DrawingTemplateWithRestrictedAccess):
    """
    Use a star notation instead list to match any role
    """
    role_id_list: list[int] | str = '*'

    async def check_access(self, session: AsyncSession, user: User, **context) -> bool:
        user_role: UserRole = await user.get_role(session)
        if type(self.role_id_list) == str and self.role_id_list == '*':
            return True

        return user_role.id in self.role_id_list


@dataclass
class TemplateCategory:
    id: int
    name: str
    templates: dict[str, DrawingTemplateRestrictedByRole]


class TemplateCategoryWithRestrictedAccess(TemplateCategory):

    @abc.abstractmethod
    async def check_access(self, **context) -> bool:
        raise NotImplemented


@dataclass
class TemplateCategoryRestrictedByUserID(TemplateCategoryWithRestrictedAccess):

    async def check_access(self, user: User, session: AsyncSession, **context) -> bool:
        res = await DrawingCategoryAllowedUsers.exists(
            category_id=self.id,
            user_id=user.id,
            session=session
        )
        return res


@dataclass
class TemplateCategoryRestrictedByRole(TemplateCategoryWithRestrictedAccess):
    """
    Use a star notation instead list to match any role
    """
    role_id_list: list[int] | str = '*'

    async def check_access(self, session: AsyncSession, user: User, **context) -> bool:
        user_role: UserRole = await user.get_role(session)
        if type(self.role_id_list) == str and self.role_id_list == '*':
            return True

        return user_role.id in self.role_id_list


class DrawWizardMenu(DynamicMenu):
    static_text = '*🎨 Выбери категорию*'
    callback_key = 'draw_wizard'
    parse_mode = 'MARKDOWNV2'
    # images = ['assets/img/gui/draw_wizard_logo.jpg']

    selected_ticket_template = StateVar('draw_wizard_selected_ticket_template', default='не выбран')
    categories: dict[str, TemplateCategoryRestrictedByRole] = {
        category.name: category
        for category in [
            TemplateCategoryRestrictedByRole(
                id=1,
                name='🎟 Билеты',
                templates={
                    'cinema': DrawingTemplateRestrictedByRole(
                        CinemaTicket,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Комната\n"
                        "📌 Стоимость\n"
                        "📌 Дата\n\n"
                        "Пример: \n\n"
                        "`Розовая\n2490\n25 мая, 19:00`",

                        '🎥 Кино'
                    ),
                    'theatre_new': DrawingTemplateRestrictedByRole(
                        TheatreTicket,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Спектакль\n"
                        "📌 Стоимость\n"
                        "📌 Место\n"
                        "📌 Дата\n\n"
                        "Пример: \n\n"
                        "`Горгоны\n2490\n5 ряд, 9 место\n25 мая, 19:00`",

                        '🎭 Театр'
                    ),
                    'exhibitions': DrawingTemplateRestrictedByRole(
                        ExhibitionTicket,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Название выставки\n"
                        "📌 Стоимость\n"
                        "📌 Дата\n"
                        "📌 Время\n\n"
                        "Пример: \n\n"
                        "`Люди и Космос\n2490\n25.09.2023\n19:00`",

                        '🏺 Выставки'
                    ),
                    'standup': DrawingTemplateRestrictedByRole(
                        StandupTicket,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Название мероприятия\n"
                        "📌 Стоимость\n"
                        "📌 Дата\n"
                        "📌 Время\n\n"
                        "Пример: \n\n"
                        "`Нурлан Сабуров\n2490\n25.09.2023\n19:00`",

                        '🎤 Стендап'
                    ),
                },
            ),
            TemplateCategoryRestrictedByUserID(
                id=2,
                name='🆘 ТП',
                templates={
                    'without_hashtag': DrawingTemplateRestrictedByRole(
                        SupportMessageWithoutHashtagTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Время\n"
                        "📌 Сумма\n"
                        "📌 Домен сайта\n\n"
                        "Пример: \n\n"
                        "`13:00 \n4999\ntheatre.com`",

                        '# Без решетки',
                        preview_images=[
                            'assets/img/support_worker/without_hashtag_example_1.png',
                            'assets/img/support_worker/without_hashtag_example_2.png',
                        ]
                    ),
                    'with_hashtag': DrawingTemplateRestrictedByRole(
                        SupportMessageWithRedundantHashtagTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Время\n"
                        "📌 Сумма\n"
                        "📌 Домен сайта\n\n"
                        "Пример: \n\n"
                        "`13:00 \n4999\ntheatre.com`",

                        '# Лишняя решетка',
                        preview_images=[
                            'assets/img/support_worker/with_hashtag_example_1.png',
                            'assets/img/support_worker/with_hashtag_example_2.png',
                        ]
                    ),
                    'without_order_n': DrawingTemplateRestrictedByRole(
                        SupportWithoutOrderNumberTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Время\n"
                        "📌 Сумма\n"
                        "📌 Домен сайта\n\n"
                        "Пример: \n\n"
                        "`13:00 \n4999\ntheatre.com`",

                        'Не указан номер',
                        preview_images=[
                            'assets/img/support_worker/without_order_num_example.png',
                        ]
                    ),
                    'refund_terms': DrawingTemplateRestrictedByRole(
                        SupportRefundTermsTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Время\n"
                        "📌 Домен сайта\n\n"
                        "Пример: \n\n"
                        "`13:00 \ntheatre.com`",

                        'Условия ВЗ',
                        preview_images=[
                            'assets/img/support_worker/refund_terms_example_1.png',
                            'assets/img/support_worker/refund_terms_example_2.png',
                        ]
                    )
                }
            ),
            TemplateCategoryRestrictedByRole(
                id=3,
                name='🌐 Сайт',
                templates={
                    # 'note': DrawingTemplateRestrictedByRole(
                    #     PaymentSystemNoteTemplate,
                    #     '*📝 Отправь мне время для отрисовки*\n\n'
                    #     'ℹ️ _*Теперь шаблоны из этой категории заполняют домен платежной системы автоматически, '
                    #     'от тебя требуется только время*_\n\n'
                    #     '🔎 *Пример:* `13:00`',
                    #     'Поле примечание',
                    #     preview_images=['assets/img/payment_sys/note_example.png']
                    # ),
                    'refund_success': DrawingTemplateRestrictedByRole(
                        PaymentSystemRefundSuccessTemplate,
                        '*📝 Отправь мне время для отрисовки*\n\n'
                        'ℹ️ _*Теперь шаблоны из этой категории заполняют домен платежной системы автоматически, '
                        'от тебя требуется только время*_\n\n'
                        '🔎 *Пример:* `13:00`',

                        'Успех ВЗ',
                        preview_images=['assets/img/payment_sys/refund_success.PNG']
                    ),
                    'non_equivalently': DrawingTemplateRestrictedByRole(
                        PaymentSystemNonEquivalently,
                        '*📝 Отправь мне время для отрисовки*\n\n'
                        'ℹ️ _*Теперь шаблоны из этой категории заполняют домен платежной системы автоматически, '
                        'от тебя требуется только время*_\n\n'
                        '🔎 *Пример:* `13:00`',

                        'Не эквивалент',
                        preview_images=['assets/img/payment_sys/not_equivalently.PNG']
                    ),
                    'transaction_restricted': DrawingTemplateRestrictedByRole(
                        PaymentSystemTransactionRestricted,
                        '*📝 Отправь мне время для отрисовки*\n\n'
                        'ℹ️ _*Теперь шаблоны из этой категории заполняют домен платежной системы автоматически, '
                        'от тебя требуется только время*_\n\n'
                        '🔎 *Пример:* `13:00`',

                        '900',
                        preview_images=['assets/img/payment_sys/transaction_restricted.PNG']
                    ),
                    'unknown_error': DrawingTemplateRestrictedByRole(
                        PaymentSystemUnknownError,
                        '*📝 Отправь мне время для отрисовки*\n\n'
                        'ℹ️ _*Теперь шаблоны из этой категории заполняют домен платежной системы автоматически, '
                        'от тебя требуется только время*_\n\n'
                        '🔎 *Пример:* `13:00`',

                        'Неизветсная ошибка',
                        preview_images=['assets/img/payment_sys/unknown_error.PNG']
                    ),
                    'card_not_supported': DrawingTemplateRestrictedByRole(
                        PaymentSystemCardNotSupported,
                        '*📝 Отправь мне время для отрисовки*\n\n'
                        'ℹ️ _*Теперь шаблоны из этой категории заполняют домен платежной системы автоматически, '
                        'от тебя требуется только время*_\n\n'
                        '🔎 *Пример:* `13:00`',

                        'Карта не поддерживается',
                        preview_images=['assets/img/payment_sys/card_not_supported.PNG']
                    ),
                    'incorrect_order_number': DrawingTemplateRestrictedByRole(
                        PaymentSystemIncorrectOrderNumber,
                        '*📝 Отправь мне время для отрисовки*\n\n'
                        'ℹ️ _*Теперь шаблоны из этой категории заполняют домен платежной системы автоматически, '
                        'от тебя требуется только время*_\n\n'
                        '🔎 *Пример:* `13:00`',

                        'Неверный номер',
                        preview_images=['assets/img/payment_sys/incorrect_order_number.PNG']
                    ),

                }
            ),
            TemplateCategoryRestrictedByRole(
                id=4,
                name='🏦 Банк',
                templates={
                    'tinkoff_income': DrawingTemplateRestrictedByRole(
                        TinkoffIncomePaymentTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Время\n"
                        "📌 Сумма\n"
                        "📌 Дата\n"
                        "📌 Имя\n"
                        "📌 Имя платежа\n"
                        "Пример: \n\n"
                        "`13:31 \n4999\n25.04\nПетр Сидоров\nПлатежи`",

                        'Тинькоф получение',
                    ),
                    'tinkoff_outcome': DrawingTemplateRestrictedByRole(
                        TinkoffOutgoingPaymentTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Время\n"
                        "📌 Сумма\n"
                        "📌 Баланс\n"
                        "📌 Карта\n"
                        "📌 Имя\n"
                        "Пример: \n\n"
                        "`13:31 \n4999\n50000\n2222333344445555\nИ. В. Иванов`",

                        'Тинькоф перевод',
                    ),
                }
            ),
            TemplateCategoryRestrictedByRole(
                id=5,
                name='📣 Саппорт',
                templates={
                    'guarantee_default': DrawingTemplateRestrictedByRole(
                        DefaultGuaranteeLetterTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Дата\n"
                        "📌 Год\n"
                        "📌 Инициалы саппорта\n"
                        "📌 Инициалы мамонта\n"
                        "📌 Сумма\n"
                        "📌 Сайт\n"
                        "Пример: \n\n"
                        "`13 Дек. \n23\nИванов Иван\nПетр Сидоров\n4999\ntheatre.com`",

                        '📜 Гарантийное обычное',
                        role_id_list=UserRoles.SUPER_ROLE_ID_LIST,
                        preview_images=['assets/img/support/guarantee_letter_default_example.png']
                    ),
                    'guarantee_cb': DrawingTemplateRestrictedByRole(
                        CbGuaranteeLetterTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Дата\n"
                        "📌 Год\n"
                        "📌 Инициалы мамонта\n"
                        "📌 Сумма\n"
                        "Пример: \n\n"
                        "`13 Дек. \n23\nИванов Иван\n4999`",

                        '🏦 Гарантийное ЦБ',
                        role_id_list=UserRoles.SUPER_ROLE_ID_LIST,
                        preview_images=['assets/img/support/guarantee_letter_cb_example.png']
                    ),
                    'refund_status': DrawingTemplateRestrictedByRole(
                        RefundStatusTemplate,
                        "📝 Отправь мне данные для отрисовки\n\n"
                        "Формат: \n\n"
                        "📌 Дата\n"
                        "📌 Инициалы мамонта\n"
                        "📌 Причина\n"
                        "Пример: \n\n"
                        "`20.12.2023\nИванов Иван\nЗапрос возврата клиентом`",

                        '♻️ Статус возврата',
                        role_id_list=UserRoles.SUPER_ROLE_ID_LIST,
                        preview_images=['assets/img/support/refund_status_example.png']
                    ),
                },
                role_id_list=UserRoles.SUPER_ROLE_ID_LIST
            ),
        ]
    }

    @classmethod
    async def _get_keyboard(cls, user: User, session: AsyncSession, **kwargs):
        available_categories_for_user = {
            category_name: category
            for category_name, category in cls.categories.items()
            if await category.check_access(user=user, session=session)
        }

        keyboard_markup = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text=category.name,
                                     callback_data=cls._generate_callback('open_cat', category_name))
            ]
                for category_name, category in available_categories_for_user.items()
            ],
            row_width=1
        )
        return keyboard_markup

    @classmethod
    async def open_category(cls, call: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
        if 'category' in kwargs:
            category_name = kwargs.pop('category')
        else:
            _, _, category_name = call.data.split(':', maxsplit=2)

        current_category = cls.categories.get(category_name)

        if not current_category:
            await call.message.answer("Категория не найдена.")
            return

        # Создаем клавиатуру, добавляя кнопки для каждого шаблона
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=template.name,
                                                      callback_data=cls._generate_callback('set_tpl', category_name,
                                                                                           template_id))]
                                for template_id, template in current_category.templates.items()
                            ] + [[InlineKeyboardButton(text='🔙 Назад', callback_data='goto:DrawWizardMenu')]]
            # Кнопка "Назад"
        )
        await call.message.answer(
            text='*🎨 Выбери шаблон*',
            reply_markup=keyboard,
            parse_mode=cls.parse_mode
        )
        await call.message.delete()

    @classmethod
    async def set_template(cls, call: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
        # Извлечение имени категории и шаблона из данных обратного вызова
        _, _, category_name, template_name = call.data.split(':', maxsplit=3)
        current_category = cls.categories.get(category_name)
        current_template = current_category.templates.get(template_name)

        # Установка состояния
        await state.set_state(TemplateState.key)
        await state.set_state(WAITING_TICKET_DATA)

        # Сохранение выбранного шаблона в состоянии
        await state.update_data(selected_ticket_template=current_template)  # Сохраняем шаблон

        backward_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='🔙 Назад',
                                                   callback_data=f'goto:DrawWizardMenu:category={current_category.name}')]]
        )

        # Отправка пользователю выбранного шаблона
        if current_template.preview_images:
            if len(current_template.preview_images) > 1:
                media = [
                    InputMediaPhoto(
                        media=img_path,
                        caption=current_template.description if img_id == 0 else None,
                        parse_mode='MARKDOWNV2'
                    )
                    for img_id, img_path in enumerate(current_template.preview_images)
                ]
                await call.message.answer_media_group(media)
            else:
                await call.message.answer_photo(
                    photo=FSInputFile(current_template.preview_images[0]),
                    reply_markup=backward_keyboard,
                    parse_mode='MARKDOWNV2',
                    caption=current_template.description
                )
            await call.message.delete()
        else:
            await call.message.edit_text(
                text=current_template.description,
                parse_mode='MARKDOWNV2',
                reply_markup=backward_keyboard
            )

    @classmethod
    async def generate_image(cls, message: Message, state: FSMContext, session: AsyncSession, **kwargs):
        ticket_data = message.text.split('\n')
        data = await state.get_data()
        selected_template = data.get('selected_ticket_template')

        if not selected_template or selected_template == 'не выбран':
            await message.reply(text='<b>⛔️ Шаблон не выбран</b>', parse_mode='HTML')
            return

        if not isinstance(selected_template, DrawingTemplate):
            await message.reply(
                text='<b>⛔️ Пожалуйста, выберите корректный шаблон</b>',
                parse_mode='HTML'
            )
            return

        try:
            drawing_template: Type[TicketTemplateT] = selected_template.template_drawer_cls(*ticket_data, session)
            print(drawing_template)
        except TypeError as e:
            print(e)
            await message.reply(
                text='<b>⛔️ Неверный формат данных</b>',
                parse_mode='HTML'
            )
            return

        try:
            drawing_result = await drawing_template.generate()  # Это должно возвращать объект BytesIO
            logging.info(f"drawing_result type: {type(drawing_result)}")  # Проверяем тип

            if isinstance(drawing_result, list):
                media = [InputMediaPhoto(media=raw_image) for raw_image in drawing_result]
                await message.answer_media_group(media)
            elif isinstance(drawing_result, io.BytesIO):
                drawing_result.seek(0)  # Сбросить указатель на начало
                # Создаем BufferedInputFile с использованием BytesIO
                buffered_file = BufferedInputFile(drawing_result.read(), filename='drawing.png')
                await message.answer_photo(buffered_file, caption='Here is your drawing!')
            else:
                # Обрабатываем случай, когда drawing_result ожидается как путь к файлу или URL
                await message.answer_photo(BufferedInputFile(drawing_result.read(), filename='drawing.png'), caption='Here is your drawing!')

        except Exception as e:
            logging.error(f"Error generating image: {e}")
            await message.reply(text='<b>⛔️ Произошла ошибка при генерации изображения</b>', parse_mode='HTML')
        finally:
            pass  # Здесь не очищаем состояние

    @classmethod
    async def hook_process_backward_buttons(cls, call: CallbackQuery, state: FSMContext, context):
        if 'category' in context:
            await cls.open_category(call, state, **context)
            raise StopRender

    @classmethod
    def register_handlers(cls, dp: Dispatcher):
        dp.register_callback_query_handler(
            cls.open_category,
            lambda call: call.data.startswith(cls._generate_callback('open_cat')),
            state='*'
        )
        dp.register_callback_query_handler(
            cls.set_template,
            lambda call: call.data.startswith(cls._generate_callback('set_tpl')),
            state='*'
        )
        dp.register_message_handler(
            cls.generate_image,
            state=WAITING_TICKET_DATA
        )

        # Handler for backward navigation
        dp.register_callback_query_handler(
            cls.hook_process_backward_buttons,
            lambda call: call.data.startswith('goto:'),
            state='*'
        )

    @classmethod
    def setup_hooks(cls):
        cls.set_hook(MenuHook.BeforeRender, cls.hook_process_backward_buttons)
