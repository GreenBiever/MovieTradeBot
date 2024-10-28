from typing import Union

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputFile

from .base import Menu


class MediaMenu(Menu):

    photo_path: Union[str, None] = None

    @classmethod
    def _get_handler_mapping(cls, target: Union[Message, CallbackQuery]) -> dict:
        return {
            False: target.answer_photo if isinstance(target, Message) else target.message.answer_photo,
            True: target.edit_media if isinstance(target, Message) else target.message.edit_media
        }

    @classmethod
    async def render(cls, initiator: Union[Message, CallbackQuery], state: FSMContext, **kwargs):
        """
        DEPRECATED
        """
        handler = cls._get_answer_handler(target=initiator)

        if cls.photo_path is None:
            raise AttributeError("Empty photo input file")

        return await handler(
            photo=InputFile(cls.photo_path),
            caption=await cls._get_text(**kwargs),
            reply_markup=await cls._get_keyboard(**kwargs),
            parse_mode=cls.parse_mode
        )
