from aiogram import Dispatcher as AiogramDispatcher, Bot
from aiogram.types import User

from aiogram_toolbet.new_version.event.processor import EventProcessor
from aiogram_toolbet.new_version.menu.keyboard import KeyboardBuilder
from aiogram_toolbet.new_version.menu.menu import Menu
from aiogram_toolbet.new_version.registry.registry import MenuRegistry


class MenuDispatcher:
    root_callback_key: str = 'mp'
    root_shortcut_callback_key = 'mp-sh'

    def __init__(self, aiogram_dispatcher: AiogramDispatcher):
        self._aiogram_dispatcher = aiogram_dispatcher
        self._registry = MenuRegistry()
        self._events = EventProcessor(self, self._registry, self._aiogram_dispatcher, shortcuts_enabled=True)

        self._register_handlers()

    async def open_menu(self, menu: Menu, in_message: int = None, **context):
        bot, user = Bot.get_current(), User.get_current()
        text = await menu.get_text(**context)
        keyboard = await menu.get_keyboard(**context)

        await keyboard.load_elements(**context)
        keyboard_builder = KeyboardBuilder(
            keyboard.elements, menu, self.root_callback_key, self._events
        )
        aiogram_keyboard = keyboard_builder.build()
        #print(aiogram_keyboard)
        self._registry.set_display_state(user.id, menu.id, keyboard_builder.get_elements_indexes())

        opening_context = {
            'text': text,
            'reply_markup': aiogram_keyboard,
            'parse_mode': menu.parse_mode
        }
        open_menu = bot.edit_message_text(
            chat_id=user.id,
            message_id=in_message,
            **opening_context
        ) if in_message else bot.send_message(
            chat_id=user.id,
            **opening_context
        )

        return await open_menu

    def set_aiogram_dispatcher(self, dp: AiogramDispatcher):
        self._aiogram_dispatcher = dp

    def register_menu(self, menu: Menu):
        self._registry.register(menu)

    def _register_handlers(self):
        self._events.register_menu_processor()
