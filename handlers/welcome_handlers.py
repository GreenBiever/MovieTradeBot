from aiogram.filters import StateFilter, Command
from aiogram import F, Router
import config
from aiogram.types import Message
from aiogram import types, exceptions, Bot
from keyboards import keyboard
from databases.models import User
from middlewares.user_middlware import AuthorizeMiddleware

from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())


async def get_greeting(message: Message, user: User, edited_message: Message | None = None):
    text = 'Привет'
    kb = await keyboard.get_webapp_kb(user.tg_id)
    if edited_message is None:
        await message.answer(text, reply_markup=kb,
                             parse_mode='HTML')
    else:
        await edited_message.edit_text(text, reply_markup=kb, parse_mode='HTML')


@router.message(Command('start'))
async def cmd_start(message: Message, bot: Bot, user: User):
    await get_greeting(message, user)
