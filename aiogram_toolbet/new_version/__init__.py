from aiogram import Dispatcher as AiogramDispatcher
from aiogram_toolbet.new_version.dispatcher.dispatcher import MenuDispatcher

_dispatcher: MenuDispatcher | None = None
_aiogram_dispatcher: AiogramDispatcher | None = None
_setup = False

root_callback_key = 'mp'


class PackageSetup:
    pass


def get_menu_dispatcher() -> MenuDispatcher:
    global _setup, _dispatcher
    if not _setup:
        raise Exception('Aiogram dispatcher not provided, use setup function to configure it')

    return _dispatcher


def setup(dp: AiogramDispatcher):
    global _aiogram_dispatcher, _dispatcher, _setup
    if _setup:
        raise Exception('Dispatcher already initialized')

    _aiogram_dispatcher = dp
    _dispatcher = MenuDispatcher(_aiogram_dispatcher)
    _setup = True
