from typing import Any, Optional
from aiogram.dispatcher import FSMContext
from aiogram.types import User
from app_dependency import get_dispatcher


class StateVar:

    STORAGE_KEY = 'state_vars'

    def __init__(self, name: str, default: Optional[Any] = None):
        self._name = name
        self._default = default

    async def get(self) -> Any:
        if not await self._is_storage_inited():
            await self._init_storage()

        async with self._get_user_state().proxy() as state:
            return state[self.STORAGE_KEY].get(self._name, self._default)

    async def set(self, value: Any) -> Any:
        if not await self._is_storage_inited():
            await self._init_storage()

        async with self._get_user_state().proxy() as state:
            state[self.STORAGE_KEY][self._name] = value

        return value

    @classmethod
    def _get_user_state(cls) -> FSMContext:
        user = User.get_current()
        dp = get_dispatcher()

        return dp.current_state(chat=user.id)

    @classmethod
    async def _is_storage_inited(cls) -> bool:
        async with cls._get_user_state().proxy() as state:
            return cls.STORAGE_KEY in state.keys()

    @classmethod
    async def _init_storage(cls):
        async with cls._get_user_state().proxy() as state:
            state[cls.STORAGE_KEY] = {}
