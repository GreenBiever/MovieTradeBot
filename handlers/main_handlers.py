from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InputMedia, InputFile
from databases.models import User
from middlewares.user_middlware import AuthorizeMiddleware
from keyboards import keyboard
import config

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())


class TicketData(StatesGroup):
    ticket_data = State()


@router.message(F.text == '💎 Главное меню')
async def main_menu(message: Message, user: User):
    kb = await keyboard.get_webapp_kb(user.tg_id)
    await message.answer(text='DIAMOND APP', reply_markup=kb)


@router.message(F.text == 'Мои ссылки')
async def my_links(message: Message, user: User):
    await message.answer(text='Ваши ссылки')


@router.message(F.text == 'Отрисовка')
async def my_drawer(message: Message, state: FSMContext):
    await message.answer(text='''<b>На данный момент доступна только отрисовка билета</b>\n\n
📝 Отправь мне данные для отрисовки
Формат: 

📌 Комната
📌 Стоимость
📌 Дата

Пример: 

Розовая
2490
25 мая, 19:00''', parse_mode='HTML')
    await state.set_state(TicketData.ticket_data)


@router.message(StateFilter(TicketData.ticket_data))
async def my_drawer(message: Message, state: FSMContext, user: User):
    await generate_image(message.text)


async def generate_image(cls, message: Message):
    ticket_data = message.text.split('\n')
    selected_template = await cls.selected_ticket_template.get()

    try:
        drawing_template = selected_template.template_drawer_cls(*ticket_data)
    except TypeError:
        await message.reply(
            text='<b>⛔️ Неверный формат данных</b>',
            parse_mode='HTML'
        )
    else:
        drawing_result = await drawing_template.generate()

        if isinstance(drawing_result, list):
            await message.answer_media_group(InputMedia(media=raw_image) for raw_image in drawing_result)
        else:
            await message.answer_photo(InputFile(drawing_result))

        await message.bot.send_message(
            chat_id=config.Chat.CHAT_DRAWING_LOGS,
            text=f'<b>🔔 ⬇️ Новая отрисовка ⬇️\n\n'
                 f'🥷 Юзер: @{message.from_user.username}\n'
                 f'📜 Шаблон: <u>{selected_template.name}</u></b>',
            parse_mode="HTML"
        )
