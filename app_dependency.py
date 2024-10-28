from aiogram.fsm.storage.memory import MemoryStorage

import config

from aiogram import Bot
from aiogram import Dispatcher


bot = Bot(config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


def get_bot() -> Bot:
    return bot


def get_storage() -> MemoryStorage:
    return storage


def get_dispatcher() -> Dispatcher:
    return dp
