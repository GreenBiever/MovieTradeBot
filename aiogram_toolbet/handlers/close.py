from contextlib import suppress

from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageCantBeDeleted


async def close_callback(call: CallbackQuery, **kwargs):
    with suppress(MessageCantBeDeleted):
        await call.message.delete()
