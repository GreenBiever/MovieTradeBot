from contextlib import suppress
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageCantBeDeleted


async def delete_message(call: CallbackQuery, **kwargs):
    with suppress(MessageCantBeDeleted):
        await call.message.delete()


async def ignore_callback_query(call, *args, **kwargs):
    await call.answer(cache_time=60)
