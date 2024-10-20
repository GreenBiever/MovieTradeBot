from aiogram import Bot
from fastapi import APIRouter

import config

bot: Bot = Bot(config.BOT_TOKEN)
router = APIRouter()


