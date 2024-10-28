from enum import Enum
from typing import TypeVar, Optional, TypeAlias, Union, TYPE_CHECKING
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_toolbet.new_version.event.hadler import HasEventHandler

if TYPE_CHECKING:
    from aiogram_toolbet.new_version.menu.menu import Menu
    from aiogram_toolbet.new_version.event.processor import EventProcessor


ButtonT = TypeVar('ButtonT', bound='Button')
ElementID: TypeAlias = Union[str, int, None]
ComponentT = TypeVar('ComponentT', bound='Component')
KeyboardElementT = TypeVar('KeyboardElementT', bound='KeyboardElementBase')
KeyboardElementGroupT = TypeVar('KeyboardElementGroupT', bound='KeyboardElementGroup')


class GroupOrientation(Enum):
    VERTICAL = 1
    HORIZONTAL = 2


class GroupBuildState:

    def __init__(self):
        self._state = []

    @property
    def state(self) -> list:
        return self._state

    def add_buttons(self, *buttons: InlineKeyboardButton, orientation: GroupOrientation = GroupOrientation.VERTICAL):
        if orientation == GroupOrientation.VERTICAL:
            self._state.extend([
                [button] for button in buttons
            ])
        elif orientation == GroupOrientation.HORIZONTAL:
            self._state.append([button for button in buttons])


class KeyboardBuilder:

    def __init__(
        self, elements: ButtonT | KeyboardElementGroupT, menu: 'Menu', menu_dispatcher_callback_key: str,
        event_processor: 'EventProcessor'
    ):
        self._elements = elements
        self._menu = menu
        self._event_processor = event_processor
        self._menu_dispatcher_callback_key = menu_dispatcher_callback_key
        self._root_path = [menu_dispatcher_callback_key, menu.id]
        self._current_path = self._root_path.copy()
        self._build_state = []
        self._elements_indexed = {}

    def build(self):
        for element in self._elements:
            if element.id is not None and element.id in self._elements_indexed.keys():
                raise AttributeError('Element building error! ID of element should be unique')

            if element.id is not None:
                self._elements_indexed[element.id] = element

            if isinstance(element, Button):
                self._mount_buttons(self._create_inline_button(element))
            elif isinstance(element, KeyboardElementGroup):
                self._mount_group_recursive(element)

        return InlineKeyboardMarkup(inline_keyboard=self._build_state)

    def get_elements_indexes(self) -> dict:
        return self._elements_indexed

    def _mount_buttons(self, *buttons: InlineKeyboardButton, orientation: GroupOrientation = GroupOrientation.VERTICAL):
        if orientation == GroupOrientation.VERTICAL:
            self._build_state.extend([
                [button] for button in buttons
            ])
        elif orientation == GroupOrientation.HORIZONTAL:
            self._build_state.append([button for button in buttons])

    def _mount_group_recursive(self, group: KeyboardElementGroupT):
        local_build_state = []
        self._current_path.append(group.id)

        for element in group.children:
            if element.id is not None and element.id in self._elements_indexed.keys():
                raise AttributeError('Element building error! ID of element should be unique')

            if element.id is not None:
                self._elements_indexed[element.id] = element

            if isinstance(element, Button):
                button = self._create_inline_button(element)
                local_build_state.append(button)
            elif isinstance(element, KeyboardElementGroup):
                self._mount_group_recursive(element)

        self._current_path.pop()
        local_build_state.reverse()

        self._mount_buttons(*local_build_state, orientation=group.orientation)

    def _create_inline_button(self, button: ButtonT) -> InlineKeyboardButton:
        callback_data = self.generate_callback_data(*self._current_path, button.on_click, button.data)
        if len(callback_data) > 64 and not self._event_processor.shortcuts_enabled:
            raise ValueError(
                'Callback data length limit reached, enable callback data shortcuts if you need callbacks > 64 chars'
            )
        elif len(callback_data) > 64 and self._event_processor.shortcuts_enabled:
            shortcut_id = self._event_processor.add_shortcut(callback_data)
            callback_data = self.generate_callback_data('mp-sh', shortcut_id)

        return InlineKeyboardButton(
            text=button.text,
            callback_data=callback_data
        )

    @classmethod
    def generate_callback_data(cls, *parts: str | int, separator: str = ':') -> str:
        return separator.join(map(str, parts))


class KeyboardElementBase:

    def __init__(self, _id: ElementID = None):
        self.id = _id

    async def build(self, **ctx) -> list[InlineKeyboardButton]:
        pass

    async def load(self, **ctx):
        await self._load(**ctx)

    async def _load(self, **ctx):
        pass


class Button(KeyboardElementBase):

    def __init__(
        self, text: str, data: Optional[str] = None, on_click: Optional[str] = None, _id: ElementID = None
    ):
        super().__init__(_id=_id)
        self.text = text
        self.data = data
        self.on_click = on_click

    async def build(self, menu_id: str, menu_dispatcher_callback_key: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(self.text, callback_data=f'{menu_dispatcher_callback_key}:{menu_id}:{self.on_click}')

    def set_text(self, text: str):
        self.text = text

    def __str__(self):
        return f'Button(text={self.text})'

    def __repr__(self):
        return self.__str__()


class KeyboardElementGroup(KeyboardElementBase):

    def __init__(
        self,
        *elements: KeyboardElementT | KeyboardElementGroupT,
        orientation: GroupOrientation = GroupOrientation.VERTICAL,
        _id: ElementID = None
    ):
        super().__init__(_id=_id)
        self._children: list[KeyboardElementT | KeyboardElementGroupT] = list(elements)
        self.orientation = orientation

    @property
    def children(self) -> list:
        return self._children

    def get_child(self, element_id: ElementID) -> KeyboardElementT | None:
        return next(filter(lambda ch: ch.id == element_id, self._children), None)

    def add_child(self, node: KeyboardElementT):
        self._children.append(node)
        return self

    def set_children(self, children):
        self._children = children

    async def load(self, **ctx):
        await self._load(**ctx)

        for child in self.children:
            print(f'Loading child {child.__class__} for {self.id}')
            await child.load(**ctx)

    def set_orientation(self, orientation: GroupOrientation):
        self.orientation = orientation


class Component(KeyboardElementGroup, HasEventHandler):

    def __init__(self, *elements: KeyboardElementT | KeyboardElementGroupT, _id: ElementID = None, **params):
        super().__init__(*elements, _id=_id)
        self._params = params

    def get_child_components(self) -> list[ComponentT]:
        return list(filter(
            lambda child: isinstance(child, Component),
            self.children
        ))


class Keyboard:

    builder = KeyboardBuilder

    def __init__(self, *elements: ButtonT | ComponentT):
        self.elements = list(elements)

    async def load_elements(self, **ctx):
        for element in self.elements:
            await element.load(**ctx)
