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
    await message.answer(text='В разработке..')
    await state.clear()
    pass


