from enum import Enum

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram_toolbet.menu import Menu

registry = {

}


def get_menu(name: str) -> 'Menu':
    return registry.get(name)


registered_hooks = {

}
used_callbacks = set()
CALLBACK_IGNORE = '_'


class MenuHook(Enum):
    BeforeRender = 'before_render'
    AfterRender = 'after_render'
    OnKeyboardCreated = 'on_keyboard_created'


class MenuMeta(type):

    reserved_menu_names = ('Menu', 'DynamicMenu', 'MediaMenu')

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        if name in cls.reserved_menu_names:
            return

        if 'callback_key' not in namespace or namespace['callback_key'] == '' and name not in cls.reserved_menu_names:
            raise NotImplementedError(
                f"Can not register {name}\nYou should provide Callback nested class and setup prefix for your menu"
            )

        if namespace['callback_key'] in used_callbacks and namespace['callback_key'] != CALLBACK_IGNORE:
            raise Warning(f"{namespace['callback_key']} callback key already in use")

        used_callbacks.add(namespace['callback_key'])

        if name in registry.keys():
            raise NameError(f"Name {name} already exists. You should keep your menu names unique")

        if not namespace.get('DISALLOW_INDEXING'):
            registry[name] = cls
            registered_hooks[name] = {
                MenuHook.BeforeRender: [],
                MenuHook.AfterRender: [],
                MenuHook.OnKeyboardCreated: [],
            }
            print(name + f"[{namespace['callback_key']}]" + ' registered')

    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)
