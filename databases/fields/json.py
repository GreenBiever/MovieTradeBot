from typing import Any, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update


class JsonFieldUpdater:

    def __init__(self, db_instance, field_name: str):
        self._db_instance = db_instance
        self.field_name = field_name

    async def _get_current_data(self, session: AsyncSession) -> dict:
        await session.refresh(self._db_instance, [self.field_name])
        return getattr(self._db_instance, self.field_name)

    async def _save(self, session: AsyncSession, new_data: dict):
        stmt = update(type(self._db_instance)).where(
            type(self._db_instance).id == self._db_instance.id
        ).values({self.field_name: new_data})
        await session.execute(stmt)
        await session.commit()

    def _get_value_at_path(self, source: dict, path: str) -> Any:
        cur_section = source
        path_parts = path.split('.')

        for part in path_parts:
            cur_section = cur_section.get(part)
            if cur_section is None:
                raise ValueError("Path does not exist")
        return cur_section

    def _update_value_at_path(self, source: dict, path: str, value: Any) -> dict:
        path_parts = path.split('.')
        cur_section = source

        for part in path_parts[:-1]:
            if part not in cur_section or not isinstance(cur_section[part], dict):
                cur_section[part] = {}
            cur_section = cur_section[part]

        cur_section[path_parts[-1]] = value
        return source
