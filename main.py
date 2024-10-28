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
from databases.connect import init_models, dispose_engine, get_async_session
from databases.crud import init_db
from utils.get_exchange_rate import currency_exchange
from app_dependency import get_bot, get_dispatcher

bot = get_bot()
dp = get_dispatcher()


async def clear_pending_updates():
    """
    Удаляет старые вебхуки и обновления, которые могли накопиться.
    """
    # Удаляем текущий вебхук, если он установлен
    await bot.delete_webhook(drop_pending_updates=True)

    # Получаем старые обновления, чтобы очистить их из очереди
    updates = await bot.get_updates(offset=-1)
    if updates:
        logging.info(f"Очистка {len(updates)} накопленных обновлений.")


async def check_webhook_status():
    webhook_info = await bot.get_webhook_info()
    logging.info('Current webhook info: %s', webhook_info)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Очищаем все старые обновления перед установкой нового вебхука
    await clear_pending_updates()

    # Устанавливаем новый вебхук
    await bot.set_webhook(url=(config.WEBHOOK_URL + config.TELEGRAM_WEBHOOK_PATH), allowed_updates=['*'])
    bot_info = await bot.get_me()
    logging.getLogger(__name__).info(f'Бот успешно запущен: {bot_info.username}')

    # Инициализация моделей базы данных и других ресурсов
    await init_models()
    session = await get_async_session() # Use your method to get an async session
    await init_db(session)
    await currency_exchange.async_init()
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler("bot.log"),
                            logging.StreamHandler()
                        ])

    yield

    # Закрытие бота и освобождение ресурсов
    await bot.close()
    await dispose_engine()


app = FastAPI(lifespan=lifespan)


@app.post(config.TELEGRAM_WEBHOOK_PATH)
async def bot_webhook(update: dict):
    logging.info('Received webhook update: %s', update)
    telegram_update = types.Update(**update)

    try:
        await dp.feed_update(bot=bot, update=telegram_update)
        logging.info('Update processed successfully.')
    except TelegramBadRequest as e:
        logging.error('Error in bot_webhook: %s', e, stack_info=True)


if __name__ == '__main__':
    app.include_router(api_router)
    app.include_router(website_router)
    app.mount("/antimovie", StaticFiles(directory="webapp", html=True), name="static")
    app.mount("/css", StaticFiles(directory="webapp/css"), name="css")
    app.mount("/media", StaticFiles(directory="webapp/media"), name="media")

    from handlers import welcome_handlers, main_handlers

    dp.include_routers(welcome_handlers.router)
    dp.include_routers(main_handlers.router)

    uvicorn.run(app, host="0.0.0.0", port=config.WEBHOOK_PORT)
