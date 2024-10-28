from typing import Any
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from functools import partial
from . import MenuType
from . import registry
from .meta import get_menu


def __get_message(initiator_message: Message | CallbackQuery):
    return initiator_message if isinstance(initiator_message, Message) else initiator_message.message


def make_handler(from_method: str, **params):
    async def _wrapper(initiator_message: Message | CallbackQuery, state: FSMContext, **kwargs):
        message = __get_message(initiator_message)
        handler = getattr(message, from_method)
        await handler(**params)

    return _wrapper


def make_callback_handler(from_method: str, **params):
    async def _wrapper(initiator_message: Message | CallbackQuery, state: FSMContext, **kwargs):
        handler = getattr(initiator_message, from_method)
        await handler(**params)

    return _wrapper


edit_keyboard = partial(make_handler, 'edit_reply_markup')
delete_message = partial(make_handler, 'delete')


def render_menu(menu_cls: MenuType | str, integrate: bool = False, **params):
    if isinstance(menu_cls, str):
        menu_cls = get_menu(menu_cls)

    async def _wrapper(initiator_message: Message | CallbackQuery, state: FSMContext, **kwargs):
        kwargs.update(params)
        return await menu_cls.render(initiator_message, state=state, **kwargs) if not integrate else await menu_cls.render_in(
            initiator_message, state=state, **kwargs
        )

    return _wrapper


def set_state(new_state: Any):
    async def _wrapper(initiator_message: Message | CallbackQuery, state: FSMContext, **kwargs):
        await state.set_state(new_state)

    return _wrapper


async def goto_handler(call: CallbackQuery, state: FSMContext, **kwargs):

    if not isinstance(call, CallbackQuery):
        raise AttributeError("goto_handler allow only CallbackQuery objects processing")

    _, menu_key, *args = call.data.split(':')
    menu_cls = registry[menu_key]
    kwargs.update({
        arg.split('=')[0]: arg.split('=')[1] for arg in args
    })

    await menu_cls.render_in(call, state, **kwargs)


def wrap_handler(handler: callable, **params):
    async def _wrapper(initiator_message: Message | CallbackQuery, state: FSMContext, **kwargs):
        await handler(**params)

    return _wrapper


def chained_handler(*handlers: callable):
    async def _wrapper(initiator_message: Message | CallbackQuery, state: FSMContext, **kwargs):
        for handler in handlers:
            await handler(initiator_message, state, **kwargs)

    return _wrapper
