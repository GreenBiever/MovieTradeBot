from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo,
                           ReplyKeyboardMarkup, KeyboardButton)
from databases.models import User
import config


async def get_webapp_kb(user_id):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text='WebApp запуск',
            web_app=WebAppInfo(url=f'{config.WEBHOOK_URL}/?id={user_id}')
        )
    )
    return kb.as_markup()
