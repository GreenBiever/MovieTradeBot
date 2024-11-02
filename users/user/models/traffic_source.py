from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from databases.models import TrafficSource as TrafficSourceORMModel


class TrafficSource:

    def __init__(self, traffic_source_orm_instance: TrafficSourceORMModel):
        self._traffic_source_orm_instance = traffic_source_orm_instance

    @classmethod
    async def create(cls, session: AsyncSession, name: str, description: Optional[str] = None) -> 'TrafficSource':
        traffic_source_orm_instance = TrafficSourceORMModel(name=name, description=description)
        session.add(traffic_source_orm_instance)
        await session.commit()
        return cls(traffic_source_orm_instance)

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List['TrafficSource']:
        result = await session.execute(select(TrafficSourceORMModel))
        return [cls(row[0]) for row in result.all()]

    @classmethod
    def from_db_instance(cls, traffic_source_orm_instance: TrafficSourceORMModel) -> 'TrafficSource':
        return cls(traffic_source_orm_instance)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, traffic_source_id: int) -> Optional['TrafficSource']:
        result = await session.execute(
            select(TrafficSourceORMModel).where(TrafficSourceORMModel.id == traffic_source_id))
        traffic_source = result.scalar_one_or_none()
        return cls.from_db_instance(traffic_source) if traffic_source else None

    @property
    def id(self) -> int:
        return self._traffic_source_orm_instance.id

    @property
    def name(self) -> str:
        return self._traffic_source_orm_instance.name

    @property
    def description(self) -> Optional[str]:
        return self._traffic_source_orm_instance.description

    async def delete(self, session: AsyncSession):
        await session.delete(self._traffic_source_orm_instance)
        await session.commit()

    async def set_name(self, session: AsyncSession, name: str):
        self._traffic_source_orm_instance.name = name
        await session.commit()

    async def set_description(self, session: AsyncSession, description: Optional[str]):
        self._traffic_source_orm_instance.description = description
        await session.commit()

    def __str__(self):
        return f"TrafficSource(id={self.id}, name='{self.name}')"

    def __repr__(self):
        return self.__str__()
