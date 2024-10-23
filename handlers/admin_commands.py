from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InputMedia, InputFile
from databases.models import User
from middlewares.user_middlware import AuthorizeMiddleware
from keyboards import keyboard
import config

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())


@router.message(F.text.startswith("/create_trafer"))
async def create_trafer(message: Message):
    pass