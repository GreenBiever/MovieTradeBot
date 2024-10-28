from typing import Union

from aiogram import Dispatcher, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMedia, InputMediaPhoto, InputFile

from .meta import MenuMeta, MenuHook, registered_hooks
from ..exceptions.helper import raise_exc
from ..exceptions.menu import StopRender


class Menu(metaclass=MenuMeta):
    """
    Base class for building custom menus.
    Inherit from this class to create your menu.

    Attributes:
        parse_mode - one of available parse modes from telegram bot api that will be applied to message
        static_text - message text
        static_keyboard - inline or reply aiogram keyboard object that will be attached to message
    """

    parse_mode: str = 'HTML'

    static_text: Union[str, None] = None
    static_keyboard: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, None] = None
    callback_key: str = ''

    DISALLOW_INDEXING = False

    @classmethod
    async def _execute_hooks(cls, key: MenuHook, *args, **kwargs):
        for hook in registered_hooks[cls.__name__][key]:
            await hook(*args, **kwargs)

    @classmethod
    def _generate_callback(cls, *parts: str | int, separator: str = ':', exclude_cls_key: bool = False) -> str:
        joined_parts = separator.join(map(str, parts))
        return f"{cls.callback_key}:{joined_parts}" if not exclude_cls_key else joined_parts

    @classmethod
    async def _get_answer_handler(cls, target: Union[Message, CallbackQuery], render_in: bool = False, **kwargs) -> callable:
        handler_map = cls._get_handler_mapping(target)
        return handler_map[render_in](
            text=await cls._get_text(**kwargs), reply_markup=await cls._get_keyboard(**kwargs), parse_mode=cls.parse_mode
        )

    @classmethod
    def _get_handler_mapping(cls, target: Union[Message, CallbackQuery]) -> dict:
        return {
            False: target.answer if isinstance(target, Message) else target.message.answer,
            True: target.edit_text if isinstance(target, Message) else target.message.edit_text
        }

    @classmethod
    async def _get_keyboard(cls, **kwargs) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, None]:
        """
        Method returns current keyboard instance that will be attached to message.
        You can override this method to provide dynamic keyboard generation.

        Examples:

        .. code-block:: python3

            async def _get_keyboard(cls):
                return InlineKeyboardMarkup(
                    inline_keyboard=[
                        InlineKeyboardButton(f'generated_btn_{i}', callback_data=f'cb_{i}') for i in range(5)
                    ]
                )


        :return: ReplyKeyboardMarkup, InlineKeyboardMarkup, None
        """
        return cls.static_keyboard if cls.static_keyboard is not None else raise_exc(NotImplementedError)

    @classmethod
    async def _on_keyboard_created(cls, kb: InlineKeyboardMarkup | ReplyKeyboardMarkup, kwargs):
        pass

    @classmethod
    async def _get_text(cls, **kwargs) -> str:
        return cls.static_text if cls.static_text is not None else raise_exc(NotImplementedError)

    @classmethod
    async def before_render(cls, initiator: Message | CallbackQuery | int, state: FSMContext | None, kwargs):
        pass

    @classmethod
    async def after_render(cls, root: Message | CallbackQuery | int, state: FSMContext | None, kwargs):
        pass

    @classmethod
    async def render(cls, initiator: Message | CallbackQuery, state: FSMContext, render_in: bool = False, **kwargs):
        try:
            return await cls._render(initiator, state, render_in, **kwargs)
        except StopRender:
            pass

    @classmethod
    async def _render(cls, initiator: Message | CallbackQuery, state: FSMContext, render_in: bool = False, **kwargs):
        await cls.before_render(initiator, state, kwargs)
        await cls._execute_hooks(MenuHook.BeforeRender, initiator, state, kwargs)

        answer_handler = await cls._get_answer_handler(target=initiator, render_in=render_in, **kwargs)
        telegram_object = await answer_handler

        await cls.after_render(telegram_object, state, kwargs)
        await cls._execute_hooks(MenuHook.AfterRender, telegram_object, state, kwargs)
        return telegram_object

    @classmethod
    async def render_in(cls, target_message: Union[Message, CallbackQuery], state: FSMContext, **kwargs):
        return await cls.render(target_message, state, render_in=True, **kwargs)

    @classmethod
    async def send(cls, chat_id: int, bot: Bot, state: FSMContext | None, **kwargs):
        await cls.before_render(chat_id, state, kwargs)
        await cls._execute_hooks(MenuHook.BeforeRender, chat_id, state, kwargs)

        keyboard = await cls._get_keyboard(**kwargs)
        keyboard = keyboard if isinstance(keyboard, InlineKeyboardMarkup) else None

        await cls._on_keyboard_created(keyboard, kwargs)
        await cls._execute_hooks(MenuHook.OnKeyboardCreated, keyboard, kwargs)

        telegram_object = await bot.send_message(
            chat_id, text=await cls._get_text(**kwargs), reply_markup=keyboard, parse_mode=cls.parse_mode
        )
        await cls._execute_hooks(MenuHook.AfterRender, telegram_object, state, kwargs)

        return telegram_object

    @classmethod
    def register_handlers(cls, dp: Dispatcher):
        """
        Abstract method for aiogram handlers registration.
        It is strongly recommended use it to separate logic in your app
        :param dp:
        :return:
        """
        pass

    @classmethod
    def setup_hooks(cls):
        pass

    @classmethod
    def register(cls, dp: Dispatcher):
        cls.register_handlers(dp=dp)
        cls.setup_hooks()

    @classmethod
    def set_hook(cls, key: MenuHook, callback: callable):
        registered_hooks[cls.__name__][key].append(callback)


class DynamicMenu(Menu):

    """
    Extended menu, that allows you to add new buttons to menu from render method.
    Just add btn_extend in you render call with list of tuples which contains buttons data.

    Examples:
        await Window.render(message, state, btn_extend=[('NewBtn1', 'new_callback_data')])
    """

    callback_key = '_'

    @classmethod
    async def _on_keyboard_created(cls, kb: InlineKeyboardMarkup | ReplyKeyboardMarkup, kwargs):
        if (buttons := kwargs.get('btn_extend', None)) is None:
            return
        kb.add(*cls.__generate_buttons(buttons))

    @classmethod
    def __generate_buttons(cls, source: list[tuple[str, str]]):
        return [
            InlineKeyboardButton(text=text, callback_data=callback_data)
            for text, callback_data in source
        ]

    @classmethod
    async def hook_state_push_buttons(cls, initiator: Message | CallbackQuery, state: FSMContext, kwargs: dict):
        async with state.proxy() as s:
            if kwargs.get('btn_extend') is not None:
                s[f'{cls.__name__}.btn_extend'] = kwargs.get('btn_extend')

            kwargs['btn_extend'] = s.get(f'{cls.__name__}.btn_extend')

    @classmethod
    def setup_hooks(cls):
        cls.set_hook(MenuHook.BeforeRender, cls.hook_state_push_buttons)


class MediaMenu(Menu):

    images: list[str] = None
    callback_key: str = ''

    @classmethod
    async def render(cls, initiator: Message | CallbackQuery, state: FSMContext, render_in: bool = False, **kwargs):
        if cls.images is None:
            raise ValueError('No images found in menu')

        return await super().render(initiator, state, render_in, **kwargs)

    @classmethod
    async def _get_answer_handler(cls, target: Union[Message, CallbackQuery], render_in: bool = False, **kwargs):
        is_media_group = len(cls.images) > 1
        message_obj = target if isinstance(target, Message) else target.message

        if render_in:
            # Редактируем сообщение с медиа
            await message_obj.edit_media(
                media=InputMediaPhoto(
                    media=cls.images[0],
                    caption=await cls._get_text(**kwargs),
                    parse_mode=cls.parse_mode,
                ),
                reply_markup=await cls._get_keyboard(**kwargs)
            )
        else:
            if is_media_group:
                # Отправка нескольких изображений как списка InputMediaPhoto
                media_list = [
                    InputMediaPhoto(media=img_path, caption=await cls._get_text(**kwargs) if idx == 0 else None,
                                    parse_mode=cls.parse_mode)
                    for idx, img_path in enumerate(cls.images)
                ]
                await target.bot.send_media_group(
                    chat_id=target.from_user.id,
                    media=media_list
                )
            else:
                # Отправка одного изображения
                await target.bot.send_photo(
                    chat_id=target.from_user.id,
                    photo=InputFile(cls.images[0]),
                    caption=await cls._get_text(**kwargs),
                    parse_mode=cls.parse_mode,
                    reply_markup=await cls._get_keyboard(**kwargs)
                )
