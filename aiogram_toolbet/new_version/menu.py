import asyncio

from aiogram_toolbet.new_version.event.event import Event
from aiogram_toolbet.new_version.menu.keyboard import Keyboard, Button, Component
from aiogram_toolbet.new_version.menu.menu import BaseMenu, StateVar


class SwitcherBtn(Button):

    def __init__(self):
        super().__init__('Вкл', data='0')

    async def _load(self, **ctx):
        print(f'Element {self.__class__.__name__} loading')
        enabled: float = ctx.get('enabled')
        text = 'Вкл' if not enabled else 'Выкл'
        self.set_text(text)

    @staticmethod
    async def on_click(event: Event):
        pass


class MentorList(Component):
    enabled = StateVar(0)

    def __init__(self, _id: str, index: int | None = None):
        super().__init__(
            Button('Развернуть', _id='expand'), _id=_id
        )
        # self.set_orientation(NodeOrientation.HORIZONTAL)

    @staticmethod
    async def handler__toggle():
        pass

    async def _load(self, **ctx):
        print(f'Element {self.__class__.__name__} loading')


class MyMenu(BaseMenu):
    id = 'my_menu'
    components = [
        MentorList
    ]

    @classmethod
    async def get_keyboard(cls, **ctx):
        return Keyboard(
            SwitcherBtn(),
            MentorList(
                _id='expand_mentors'
            ).add_child(
                SwitcherBtn(),
            ).add_child(
                SwitcherBtn(),
            ).add_child(
                MentorList(_id='NUMMBER_2').add_child(
                    SwitcherBtn()
                )
            )
        )

    @staticmethod
    async def handler__echo():
        pass


async def preload_kbd():
    ctx = {
        'enabled': True,
        'menu_id': MyMenu.id
    }
    keyboard = await MyMenu.get_keyboard(**ctx)
    await keyboard.preload_elements(**ctx)


asyncio.run(preload_kbd())
