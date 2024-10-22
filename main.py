import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import config
from api.external.websites_api import router as website_router
from api.main_bot_api import router as api_router
from databases.connect import init_models, dispose_engine
from handlers import welcome_handlers, main_handlers
from utils.get_exchange_rate import currency_exchange

bot: Bot = Bot(config.BOT_TOKEN)
dp = Dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(url=(config.WEBHOOK_URL + config.TELEGRAM_WEBHOOK_PATH), allowed_updates=['*'])
    bot_info = await bot.get_me()
    logging.getLogger(__name__).info(f'Бот успешно запущен: {bot_info.username}')
    await init_models()
    await currency_exchange.async_init()
    logging.basicConfig(filename="bot.log", level=logging.INFO)
    yield
    await bot.close()
    await dispose_engine()


app = FastAPI(lifespan=lifespan)


@app.post(config.TELEGRAM_WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    try:
        await dp.feed_update(bot=bot, update=telegram_update)
    except TelegramBadRequest as e:
        logging.error(e, stack_info=True)


if __name__ == '__main__':
    app.include_router(api_router)
    app.include_router(website_router)
    app.mount("/antimovie", StaticFiles(directory="webapp", html=True), name="static")
    app.mount("/css", StaticFiles(directory="webapp/css"), name="css")
    app.mount("/media", StaticFiles(directory="webapp/media"), name="media")
    dp.include_routers(welcome_handlers.router)
    dp.include_routers(main_handlers.router)
    uvicorn.run(app, host="0.0.0.0", port=config.WEBHOOK_PORT)
