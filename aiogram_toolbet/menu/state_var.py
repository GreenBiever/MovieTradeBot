import logging
from typing import Any, Optional
from aiogram.fsm.context import FSMContext


class StateVar:
    STORAGE_KEY = 'state_vars'

    def __init__(self, name: str, default: Optional[Any] = None):
        self._name = name
        self._default = default

    async def set(self, value: Any, state: FSMContext) -> Any:
        if not await self._is_storage_inited(state):
            await self._init_storage(state)

        data = await state.storage.get_data(state)
        data[self.STORAGE_KEY][self._name] = value
        await state.storage.set_data(state, data)

        logging.info(f'Setting value: {value} for key: {self._name}')  # Отладка
        return value

    async def get(self, state: FSMContext) -> Any:
        if not await self._is_storage_inited(state):
            await self._init_storage(state)

        data = await state.storage.get_data(state)
        result = data.get(self.STORAGE_KEY, {}).get(self._name, self._default)
        logging.info(f'Getting value: {result} for key: {self._name}')  # Отладка
        return result

    async def reset(self, state: FSMContext):
        await self.set(self._default, state)

    @classmethod
    async def _is_storage_inited(cls, state: FSMContext) -> bool:
        data = await state.storage.get_data(state)
        return cls.STORAGE_KEY in data

    @classmethod
    async def _init_storage(cls, state: FSMContext):
        data = await state.storage.get_data(state)
        data.setdefault(cls.STORAGE_KEY, {})
        await state.storage.set_data(state, data)


class StateVarRemote(StateVar):
    async def set(self, value: Any, state: FSMContext):
        # Реализуйте логику удаленного хранения, если это необходимо
        pass