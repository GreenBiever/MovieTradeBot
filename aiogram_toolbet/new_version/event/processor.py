import uuid
from dataclasses import dataclass
from enum import Enum

from aiogram import Dispatcher as AiogramDispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, ChatType
from typing_extensions import TYPE_CHECKING

from aiogram_toolbet.new_version.menu.keyboard import KeyboardElementGroupT, ButtonT
from aiogram_toolbet.new_version.menu.menu import Menu

if TYPE_CHECKING:
    from aiogram_toolbet.new_version import MenuDispatcher
    from aiogram_toolbet.new_version.registry.registry import MenuRegistry


class EventProcessorException(Exception):
    pass


class EventProcessingError(EventProcessorException):
    pass


class HandlerNotFound(EventProcessorException):
    pass


@dataclass
class AiogramContext:
    call: CallbackQuery
    state: FSMContext


class ClickEvent:

    def __init__(
        self,
        menu: Menu,
        sender: ButtonT | KeyboardElementGroupT,
        ctx: dict,
        aiogram_ctx: AiogramContext,
        menu_dispatcher: 'MenuDispatcher',
        sender_data: str = None,
    ):
        self.ctx = ctx
        self._menu_dispatcher = menu_dispatcher
        self.aiogram_ctx = aiogram_ctx
        self.menu = menu
        self.sender = sender
        self.data = sender_data

    async def refresh_menu(self):
        await self._menu_dispatcher.open_menu(
            self.menu, in_message=self.aiogram_ctx.call.message.message_id, **self.ctx
        )


class CallbackDataParseMode(Enum):
    DEFAULT = 1
    WITH_SHORTCUTS = 2


class CallbackDataParser:

    def __init__(self, event_processor: 'EventProcessor', call: CallbackQuery, parse_mode: CallbackDataParseMode):
        self.parse_mode = parse_mode
        self._event_processor = event_processor
        self._call = call
        self._callback_data = call.data
        self._shortcut_parsed = None

    @property
    def shortcut_parsed(self) -> str | None:
        return self._shortcut_parsed

    def parse(self) -> tuple[str, str, str, list]:
        parsers = {
            CallbackDataParseMode.DEFAULT: self._parse_default,
            CallbackDataParseMode.WITH_SHORTCUTS: self._parse_with_shortcuts
        }

        return parsers[self.parse_mode]()

    def _parse_default(self):
        _, *full_path = self._callback_data.split(self._event_processor.CALLBACK_DATA_SEP)
        menu_id, *element_path = full_path
        parent, handler_key, data = None, None, None

        for element_index, element_id in enumerate(element_path):
            component = self._event_processor.menu_registry.get_active_menu_component(
                self._call.from_user.id, menu_id, element_id
            )

            if component is None:
                handler_key = element_id
                data = element_path[element_index + 1:]
                break

            parent = element_id

        return menu_id, parent, handler_key, data

    def _parse_with_shortcuts(self):
        _, shortcut_id = self._callback_data.split(self._event_processor.CALLBACK_DATA_SEP, maxsplit=1)
        callback_data = self._event_processor.get_shortcut(shortcut_id)
        _, *full_path = callback_data.split(self._event_processor.CALLBACK_DATA_SEP)
        menu_id, *element_path = full_path
        parent, handler_key, data = None, None, None

        for element_index, element_id in enumerate(element_path):
            component = self._event_processor.menu_registry.get_active_menu_component(
                self._call.from_user.id, menu_id, element_id
            )

            if component is None:
                handler_key = element_id
                data = element_path[element_index + 1:]
                break

            parent = element_id

        return menu_id, parent, handler_key, data


class EventProcessor:

    CALLBACK_DATA_SEP = ':'

    def __init__(
        self, dispatcher: 'MenuDispatcher', registry: 'MenuRegistry', aiogram_dispatcher: AiogramDispatcher,
        shortcuts_enabled: bool = False
    ):
        self._dispatcher = dispatcher
        self._aiogram_dispatcher = aiogram_dispatcher
        self._menu_registry = registry

        self.shortcuts_enabled = shortcuts_enabled
        self._shortcuts = {}

    @property
    def menu_registry(self) -> 'MenuRegistry':
        return self._menu_registry

    def add_shortcut(self, callback_data: str):
        while (shortcut_id := str(uuid.uuid4())) in self._shortcuts.keys():
            continue

        self._shortcuts[shortcut_id] = callback_data
        return shortcut_id

    def get_shortcut(self, shortcut_id: str) -> str:
        return self._shortcuts[shortcut_id]

    def remove_shortcut(self, shortcut_id: str):
        del self._shortcuts[shortcut_id]

    def register_menu_processor(self):
        self._aiogram_dispatcher.register_callback_query_handler(
            self._handle_shortcut_interaction,
            lambda call: call.data.startswith(self._dispatcher.root_shortcut_callback_key),
            chat_type=ChatType.PRIVATE, state='*'
        )
        self._aiogram_dispatcher.register_callback_query_handler(
            self._handle_default_interaction, lambda call: call.data.startswith(self._dispatcher.root_callback_key),
            chat_type=ChatType.PRIVATE, state='*'
        )

    def _build_event(self, call: CallbackQuery, state: FSMContext, menu: Menu, ctx: dict, sender: ButtonT | KeyboardElementGroupT, sender_data: str = None) -> ClickEvent:
        return ClickEvent(
            ctx=ctx,
            menu_dispatcher=self._dispatcher,
            menu=menu,
            aiogram_ctx=AiogramContext(call, state),
            sender=sender,
            sender_data=sender_data
        )

    async def _handle_default_interaction(self, call: CallbackQuery, state: FSMContext, **kwargs):
        callback_data_parser = CallbackDataParser(self, call, CallbackDataParseMode.DEFAULT)
        menu_id, parent_id, handler_key, data = callback_data_parser.parse()

        await self._process_click_event(call, state, call.from_user.id, menu_id, handler_key, parent_id, **kwargs)

    async def _handle_shortcut_interaction(self, call: CallbackQuery, state: FSMContext, **kwargs):
        callback_data_parser = CallbackDataParser(self, call, CallbackDataParseMode.WITH_SHORTCUTS)
        menu_id, parent_id, handler_key, data = callback_data_parser.parse()

        await self._process_click_event(call, state, call.from_user.id, menu_id, handler_key, parent_id, **kwargs)

    async def _process_click_event(
        self, call: CallbackQuery, state: FSMContext, user_id: int, menu_id: str, handler_key: str,
        parent_id: str = None, **context
    ):
        handler = (
            self._menu_registry.get_menu_handler(menu_id, handler_key)
            if parent_id is None else
            self._menu_registry.get_component_handler(user_id, menu_id, parent_id, handler_key)
        )

        await handler(self._build_event(
            call,
            state,
            menu=self._menu_registry.get_menu(menu_id),
            ctx=context,
            sender=self._menu_registry.get_active_menu_component(
                call.from_user.id, menu_id, parent_id
            ),
            sender_data=None
        ))

    async def _process_event(self, menu_id: str, path: list, call: CallbackQuery, state: FSMContext, **kwargs):
        handler, last_element_id = None, None
        last_path_id = None

        for el_index, element_id in enumerate(path):
            last_path_id = el_index
            handler = self._menu_registry.get_menu_handler(menu_id, element_id, strict=False)
            if handler is not None:
                break

            last_element_id = element_id

        if handler is None:
            raise HandlerNotFound

        data = path[last_path_id + 1:]
        await handler(self._build_event(
            call,
            state,
            menu=self._menu_registry.get_menu(menu_id),
            ctx=kwargs,
            sender=self._menu_registry.get_active_menu_component(
                call.from_user.id, menu_id, last_element_id
            ),
            sender_data=data
        ))
