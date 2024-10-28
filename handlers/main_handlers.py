from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InputMedia, InputFile, FSInputFile, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from databases.models import User
from middlewares.user_middlware import AuthorizeMiddleware
from keyboards import keyboard
import config
from main import bot as Bot
from menus.draw_wizard import DrawWizardMenu
from aiogram_toolbet.menu.helper import render_menu
from app_dependency import dp as Dispatcher

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())
bot = Bot


class TicketData(StatesGroup):
    ticket_data = State()


@router.message(F.text == '💎Главное меню💎')
async def main_menu(message: Message, user: User):
    kb = await keyboard.get_webapp_kb(user.tg_id)
    await bot.send_animation(chat_id=message.from_user.id, animation=FSInputFile(config.Gifs.welcome_gif),
                             caption='DIAMOND APP', reply_markup=kb)


@router.message(F.text == '🌍Мои ссылки🌍')
async def my_links(message: Message, user: User):
    await message.answer(text='Ваши ссылки')


@router.message(F.text == '👨‍🎨Мастер отрисовки👨‍🎨')
async def my_drawer(message: Message, user: User, state: FSMContext, session: AsyncSession):
    await message.answer("Мастер отрисовки открыт.")

    # Получаем обертку для рендеринга меню
    menu_renderer = render_menu(DrawWizardMenu)

    # Вызываем обертку с нужными аргументами
    await menu_renderer(message, state=state, user=user, session=session)


@router.callback_query(F.data.startswith('draw_wizard:open_cat'))
async def open_category_handler(call: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    await call.answer()
    await DrawWizardMenu.open_category(call=call, state=state, session=session, user=user)


@router.callback_query(F.data.startswith('draw_wizard:set_tpl'))
async def set_template_handler(call: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    await call.answer()
    await DrawWizardMenu.set_template(call=call, state=state, session=session, user=user)


@router.message(StateFilter('DrawWizard:WAITING_TICKET_DATA'))
async def process_ticket_data(message: Message, state: FSMContext, user: User, session: AsyncSession):
    await DrawWizardMenu.generate_image(message=message, state=state, session=session, user=user)


@router.message(F.text == '🛡О проекте🛡')
async def my_links(message: Message, user: User):
    await message.answer(text='''<b>💎 DIAMOND TEAM 💎
    
🔰 Проект содержит в себе 3 направления:
🎭 AntiKino, 📊 Treid, 🚙 BlaBlaCar
🌍Регионы нашей работы: Россия, Украина, Казахстан, Армения, ОАЭ и многие страны Европейского союза

🌀Подробнее ознакомиться с данными направлениями вы можете в информационном разделе
📖Информационный раздел - <a href='https://t.me/+mKiPNr9IaGU1ZmNi'>ССЫЛКА</a>
🍀Информация о рангах и их повышение - <a href=''>ССЫЛКА</a>
💰Успешные транзакции - <a href=''>ССЫЛКА</a>

🧰Основной рабочий процесс производится через главное меню, WebApp.
✅ТС - @LoveSexMent</b>''', parse_mode="HTML")
