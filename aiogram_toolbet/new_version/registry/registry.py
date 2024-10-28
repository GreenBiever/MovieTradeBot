from typing import Any

from aiogram_toolbet.new_version.menu.keyboard import ComponentT, KeyboardElementT
from aiogram_toolbet.new_version.menu.menu import MenuT, Menu


class RegisteredMenu:
    pass


class RegistryException(BaseException):
    pass


class MenuNotFound(RegistryException):
    pass


class HandlerNotFound(RegistryException):
    pass


class MenuRegistry:

    def __init__(self):
        self._registry = {}
        self._display_state = {}

    def register(self, menu: Menu):
        if not self._is_registered(menu.id):
            self._registry[menu.id] = {
                'cls': menu,
                'handlers': menu.export_event_handlers(),
                'hooks': {},
            }

    def is_menu_component(self, user_id: int, menu_id: str, component_id: str) -> bool:
        try:
            self._display_state[user_id][menu_id][component_id]
        except KeyError:
            return False
        else:
            return True

    def set_display_state(self, user_id: int, menu_id: str, indexed_elements: dict[str, KeyboardElementT]):
        new_display_state = {
            user_id: {
                menu_id: {'indexed_elements': indexed_elements}
            }
        }
        if user_id not in self._display_state.keys():
            self._display_state[user_id] = {}

        self._display_state.update(new_display_state)

    def get_menu(self, menu_id: str) -> Menu:
        return self._registry[menu_id]['cls']

    def get_menu_handler(self, menu_id: str, handler_key: str, strict: bool = True) -> callable:
        if not self._is_registered(menu_id):
            raise MenuNotFound

        if (handler := self._registry[menu_id]['handlers'].get(handler_key, None)) is None and strict:
            raise HandlerNotFound

        return handler

    def get_component_handler(self, user_id: int, menu_id: str, component_id: str, handler_ley: str):
        return self._display_state[user_id][menu_id]['indexed_elements'][component_id].get_instance_event_handler(handler_ley)

    def get_active_menu_component(self, user_id: int, menu_id: str, component_id: str) -> ComponentT | None:
        try:
            return self._display_state[user_id][menu_id]['indexed_elements'][component_id]
        except KeyError:
            return None

    def _is_registered(self, menu_id: str):
        return menu_id in self._registry.keys()
