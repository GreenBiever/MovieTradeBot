from aiogram.filters import StateFilter, Command
from aiogram import F, Router
from aiogram.fsm.state import StatesGroup, State

import config
from aiogram.types import Message
from aiogram import types, exceptions, Bot
from keyboards import keyboard as kb
from databases.models import User
from middlewares.user_middlware import AuthorizeMiddleware
from databases.crud import init_db
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

router = Router()
router.message.middleware(AuthorizeMiddleware())
router.callback_query.middleware(AuthorizeMiddleware())


class SendApplication(StatesGroup):
    first_question = State()
    second_question = State()
    third_question = State()


async def get_greeting(message: Message, user: User, edited_message: Message | None = None):
    if user.status == 3:
        await message.answer('Вы заблокированы!')
        return
    if user.status == 1:
        await message.answer('Ожидайте рассмотрения вашей заявки')
        return
    if user.status == 2:
        await message.answer(text=f'<b>👋 Добро пожаловать, {user.username}!\n выберите сервис ниже:</b>',
                             parse_mode="HTML", reply_markup=kb.main)
        if user.tg_id in config.ADMIN_IDS or user.role_id == 3:
            await message.answer(text=f'<b>👋 Добро пожаловать администратор, {user.username}!\n выберите сервис ниже:</b>',
                                 parse_mode="HTML", reply_markup=kb.main_admin)
    else:
        await message.answer(text=f'<b>👋Добро пожаловать, {user.username}!\n\
    Подай заявку чтобы присоединиться к 💎Diamond Team💎</b>',
                             parse_mode="HTML", reply_markup=kb.apply)


@router.message(Command('start'))
async def cmd_start(message: Message, bot: Bot, user: User, session: AsyncSession):
    await init_db(session)
    await get_greeting(message, user)


@router.callback_query(F.data == 'apply')
async def application_start(cb: types.CallbackQuery,
                            state: FSMContext):
    await cb.message.answer(text='<b>Твоя заявка: Не заполнена\n\n'
                                 '1. ---\n'
                                 '2. ---\n'
                                 '3. ---\n\n'
                                 '🕵️ Откуда вы о нас узнали?</b>', parse_mode='HTML')
    await cb.answer()
    await state.set_state(SendApplication.first_question)


@router.message(StateFilter(SendApplication.first_question))
async def application_fist(message: Message,
                           state: FSMContext,
                           bot: Bot):
    answer = message.text
    await state.update_data(first_question=answer)
    await bot.send_message(message.from_user.id, text='<b>Твоя заявка: Не заполнена\n\n'
                                                      f'1. {answer}\n'
                                                      '2. ---\n'
                                                      '3. ---\n\n'
                                                      '🧠 Есть ли опыт работы? Если да то какой?</b>', parse_mode='HTML')
    await state.set_state(SendApplication.second_question)


@router.message(StateFilter(SendApplication.second_question))
async def application_second(message: Message,
                             state: FSMContext,
                             bot: Bot):
    answer = message.text
    state_info = await state.get_data()
    first_answer = state_info.get('first_question')
    await state.update_data(second_question=answer)
    await bot.send_message(message.from_user.id, text='<b>Твоя заявка: Не заполнена\n\n'
                                                      f'1. {first_answer}\n'
                                                      f'2. {answer}\n'
                                                      '3. ---\n\n'
                                                      '🧑‍💻 Сколько времени готовы уделять работе?</b>',
                           parse_mode='HTML')
    await state.set_state(SendApplication.third_question)


@router.message(StateFilter(SendApplication.third_question))
async def application_third(message: Message,
                            state: FSMContext,
                            bot: Bot):
    answer = message.text
    await state.update_data(third_question=answer)
    state_info = await state.get_data()
    first_answer = state_info.get('first_question')
    second_answer = state_info.get('second_question')
    await bot.send_message(message.from_user.id, text='<b>Твоя заявка: Заполнена\n\n'
                                                      f'1. {first_answer}\n'
                                                      f'2. {second_answer}\n'
                                                      f'3. {answer}\n\n'
                                                      '🧑Отправить?</b>', parse_mode='HTML',
                           reply_markup=kb.application_send)


@router.callback_query(lambda call: call.data in ['send_application', 'again'])
async def application_send(call: types.CallbackQuery,
                           state: FSMContext,
                           bot: Bot, user: User, session: AsyncSession):
    if call.data == 'send_application':
        state_info = await state.get_data()
        first_answer = state_info.get('first_question')
        second_answer = state_info.get('second_question')
        third_answer = state_info.get('third_question')
        result = await session.execute(select(User.tg_id).where(User.role_id == 3))
        admins = result.scalars().all()
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, text='Уважаемый администратор'
                                                      '\nОтправлена новая заявка на работу!!!\n\n'
                                                      f'<b>Имя пользователя:</b> <code>@{user.username}</code>\n'
                                                      f'<b>Первый ответ: {first_answer}</b>\n'
                                                      f'<b>Второй ответ: {second_answer}</b>\n'
                                                      f'<b>Третий ответ: {third_answer}</b>', parse_mode='HTML',
                                       reply_markup=kb.get_admin_accept_kb(user.tg_id))
            except exceptions.TelegramForbiddenError:
                pass
        await state.clear()
        try:
            await session.execute(
                update(User)
                .where(User.tg_id == user.tg_id)
                .values(status=1)
            )
            await session.commit()
        except Exception as e:
            print(e)
        await bot.send_message(call.from_user.id, text='✅ Ваша заявка отправлена')
    elif call.data == 'again':
        await state.clear()
        await bot.send_message(call.from_user.id,
                               text=f'<b>👋Добро пожаловать, {call.from_user.first_name} Подай заявку чтобы присоединиться к 💎Parimatch Team💎</b>',
                               parse_mode="HTML", reply_markup=kb.apply)


@router.callback_query(F.data.startswith('request_'))
async def admin_application(call: types, user: User, bot: Bot, session: AsyncSession):
    _, status, user_tg_id = call.data.split('_')
    if status == 'accept':
        await bot.send_message(user_tg_id, text='✅ Ваша заявка принята\n\n', reply_markup=kb.main)
        try:
            print(user_tg_id)
            await session.execute(
                update(User)
                .where(User.tg_id == int(user_tg_id))
                .values(status=2)
            )
            await session.commit()
        except Exception as e:
            print(e)
    elif status == 'decline':
        await bot.send_message(user_tg_id, text='✅ Ваша заявка отклонена', reply_markup=kb.main)
