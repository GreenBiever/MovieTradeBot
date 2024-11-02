from typing import Type, Iterable, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, exists
from databases.models import ProjectVar


def read_bool(value: str) -> bool:
    excepted = ('0', 'false',)
    return False if value.lower() in excepted else bool(value)


class ProjectVarServiceExc(Exception):
    pass


class VarAlreadyExists(ProjectVarServiceExc):
    pass


class VarNotExists(ProjectVarServiceExc):
    pass


class UnsupportedCastType(ProjectVarServiceExc):
    pass


class ProjectVarService:
    class Cast:
        Int = 'int'
        Float = 'float'
        Str = 'str'
        Bool = 'bool'
        List = 'list'

    cast_map = {
        Cast.Int: int, Cast.Str: str, Cast.Float: float, Cast.Bool: read_bool
    }
    CastType = str

    def __init__(self, project_var: Type[ProjectVar], session: AsyncSession):
        self._model = project_var
        self._session = session

    async def create(self, name: str, cast_type: CastType, value: str = ''):
        stmt = select(exists().where(self._model.config_key == name))
        result = await self._session.execute(stmt)
        if result.scalar():
            raise VarAlreadyExists
        elif cast_type not in self.cast_map.keys():
            raise UnsupportedCastType

        new_var = self._model(config_key=name, value=value, convert=cast_type)
        self._session.add(new_var)
        await self._session.commit()

    async def set(self, name: str, value: Union[str, int, bool, float], strict: bool = False):
        stmt = select(self._model).where(self._model.config_key == name)
        result = await self._session.execute(stmt)
        var_value = result.scalar_one_or_none()

        if var_value is None:
            if strict:
                raise VarNotExists
            await self.create(name=name, cast_type=type(value).__name__, value=str(value))
        else:
            update_stmt = update(self._model).where(self._model.config_key == name).values(value=str(value))
            await self._session.execute(update_stmt)
            await self._session.commit()

    async def get(self, *names: str) -> Union[str, int, bool, float]:
        if len(names) > 1:
            return await self.__bulk_get(*names)
        else:
            return await self.__get_one(names[0])

    async def __get_one(self, name: str) -> Union[str, int, bool, float]:
        stmt = select(self._model.value, self._model.convert).where(self._model.config_key == name)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if row is None:
            raise VarNotExists

        value, cast_type = row
        return self.__present_value(value, cast_type)

    async def __bulk_get(self, *names: str) -> Iterable[Union[str, int, bool, float]]:
        stmt = select(self._model.value, self._model.convert, self._model.config_key).where(
            self._model.config_key.in_(names))
        result = await self._session.execute(stmt)
        variables = result.fetchall()

        if not self.__contains_requested_items(names, variables):
            raise VarNotExists

        return tuple(self.__present_value(variable.value, variable.convert) for variable in variables)

    def __present_value(self, raw_value: str, cast_type: CastType) -> Union[str, int, bool, float]:
        return self.cast_map[cast_type](raw_value)

    @staticmethod
    def __contains_requested_items(var_names: Iterable[str], result_queryset: list):
        presented_variables = {variable.config_key for variable in result_queryset}
        return all(requested_var in presented_variables for requested_var in var_names)
