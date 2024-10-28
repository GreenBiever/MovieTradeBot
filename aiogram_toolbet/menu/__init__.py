from typing import TypeVar, Type, Union
from .base import Menu

from .meta import registry

MenuBase = TypeVar('MenuBase', bound=Menu)
MenuType = Union[Type[Menu], MenuBase]
