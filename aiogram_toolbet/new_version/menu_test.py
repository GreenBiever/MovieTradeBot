
from aiogram_toolbet.new_version.event.processor import ClickEvent
from aiogram_toolbet.new_version.menu.keyboard import Keyboard, Button, Component
from aiogram_toolbet.new_version.menu.menu import BaseMenu
from aiogram_toolbet.new_version.menu.state_var import StateVar


class SwitcherBtn(Button):

    def __init__(self):
        super().__init__('Вкл', data='0')

    async def _load(self, **ctx):
        enabled: float = ctx.get('enabled')
        text = 'Вкл' if not enabled else 'Выкл'
        self.set_text(text)


class ListCollapse(Component):

    expanded = StateVar('expanded', False)

    def __init__(self, _id: str, index: int | None = None):
        super().__init__(
            _id=_id
        )

    async def _load(self, **ctx):
        expanded = await self.expanded.get()
        header_txt = '🔽🔽🔽🔽🔽🔽🔽' if not expanded else '🔼🔼🔼🔼🔼🔼'
        self.add_child(Button(header_txt, on_click='expand', data='test'))

        if expanded:
            self.add_child(Button('Item 1', on_click='click_item'))
            self.add_child(Button('Item 2', on_click='click_item'))
            self.add_child(Button('Item 3', on_click='click_item'))

    @classmethod
    async def toggle(cls):
        await cls.expanded.set(not await cls.expanded.get())

    async def handler__expand(self, event: ClickEvent):
        await self.toggle()
        await event.refresh_menu()

    async def handler__click_item(self, event: ClickEvent):
        print(self)
        await event.aiogram_ctx.call.answer(
            text='Item clicked', show_alert=True, cache_time=1
        )


class MyMenu(BaseMenu):
    id = 'my_menu'
    components = [
        ListCollapse,
    ]

    @classmethod
    async def get_keyboard(cls, **ctx):
        return Keyboard(
            SwitcherBtn(),
            ListCollapse(_id='m_list').add_child(
                ListCollapse(_id='sub_m_list').add_child(
                    ListCollapse(_id='third-level-sub_m_list')
                )
            )
        )

    @classmethod
    async def _get_text(cls, **context) -> str:
        return 'Static text'

    @staticmethod
    async def handler__echo():
        pass


