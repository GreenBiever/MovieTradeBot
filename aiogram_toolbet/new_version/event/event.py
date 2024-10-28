from aiogram_toolbet.new_version.menu.keyboard import Component
from aiogram_toolbet.new_version.menu.menu import MenuT


class ButtonHandler:

    def __init__(self, component: 'Component', context: dict):
        self._component = component
        self._context = context

    @property
    def component(self):
        return self._component

    @property
    def context(self):
        return self._context


class Event:

    def __init__(self, sender: ButtonHandler, menu: MenuT):
        self.sender = sender
        self.menu = menu
