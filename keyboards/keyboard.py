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


main_kb = [
    [KeyboardButton(text="💎Главное меню💎")],
    [KeyboardButton(text="🌍Мои ссылки🌍")],
    [KeyboardButton(text='👨‍🎨Мастер отрисовки👨‍🎨'),
     KeyboardButton(text='🛡О проекте🛡')]
]

main_admin_kb = [
    [KeyboardButton(text="💎Главное меню💎")],
    [KeyboardButton(text="🌍Мои ссылки🌍")],
    [KeyboardButton(text='👨‍🎨Мастер отрисовки👨‍🎨'),
     KeyboardButton(text='🛡О проекте🛡')],
    [KeyboardButton(text='Админ-панель')]
]

main = ReplyKeyboardMarkup(keyboard=main_kb, resize_keyboard=True)
main_admin = ReplyKeyboardMarkup(keyboard=main_admin_kb, resize_keyboard=True)

apply_kb = [
    [InlineKeyboardButton(text='Подать заявку', callback_data='apply')]
]

apply = InlineKeyboardMarkup(inline_keyboard=apply_kb)

application_send_kb = [
    [InlineKeyboardButton(text='Отправить', callback_data='send_application'),
     InlineKeyboardButton(text='Заново', callback_data='again')]
]

application_send = InlineKeyboardMarkup(inline_keyboard=application_send_kb)


def get_admin_accept_kb(user_id: int):
    admin_accept_kb = [
        [InlineKeyboardButton(text='✅ Принять', callback_data=f'request_accept_{user_id}'),
         InlineKeyboardButton(text='❌ Отклонить', callback_data=f'request_decline_{user_id}')]
    ]

    admin_accept = InlineKeyboardMarkup(inline_keyboard=admin_accept_kb)
    return admin_accept
