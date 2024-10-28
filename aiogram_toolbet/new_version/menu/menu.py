from typing import TypeVar, Type
from aiogram.types import CallbackQuery, Message, ParseMode

from aiogram_toolbet.new_version.event.hadler import HasEventHandler
from aiogram_toolbet.new_version.menu.keyboard import ComponentT, Keyboard
from aiogram_toolbet.new_version.menu.meta import MenuMeta


class BaseMenu(HasEventHandler, metaclass=MenuMeta):

    id: str = ''
    parse_mode: str = ParseMode.HTML
    components: list[ComponentT] = []

    @classmethod
    def export_event_handlers(cls) -> dict[str, callable]:
        menu_handlers = cls.get_event_handlers()
        for component in cls.components:
            menu_handlers.update(component.get_event_handlers())

        return menu_handlers

    @classmethod
    async def get_keyboard(cls, **context) -> Keyboard:
        return await cls._get_keyboard(**context)

    @classmethod
    async def _get_keyboard(cls, **context) -> Keyboard:
        pass

    @classmethod
    async def get_text(cls, **context) -> str:
        return await cls._get_text(**context)

    @classmethod
    async def _get_text(cls, **context) -> str:
        pass

    @classmethod
    async def open(cls, initiator: Message | CallbackQuery, integrate: bool = False, **context):
        context.update({'menu_id': cls.id})

        text = await cls.get_text(**context)
        keyboard = await cls.get_keyboard(**context)

        await keyboard.load_elements(**context)
        aiogram_keyboard = await keyboard.build(**context)
        print(aiogram_keyboard)

        message_instance: Message = initiator if isinstance(initiator, Message) else initiator.message
        open_menu = message_instance.edit_text if integrate else message_instance.answer
        opening_context = {
            'text': text,
            'reply_markup': aiogram_keyboard,
            'parse_mode': cls.parse_mode
        }

        return await open_menu(**opening_context)


Menu = Type[BaseMenu]
MenuT = TypeVar('MenuT', bound=BaseMenu)
