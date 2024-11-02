from typing import Union

class TrafficSource:

    def __init__(self, traffic_source_db_instance):
        self._traffic_source_db_instance = traffic_source_db_instance

    @classmethod
    async def create(cls, name: str, description: str):
        from .models.traffic_source import TrafficSource as TrafficSourceDbModel  # Отложенный импорт
        return cls.from_db_instance(await TrafficSourceDbModel.create(name, description))

    @classmethod
    async def get_all(cls) -> list['TrafficSource']:
        from .models.traffic_source import TrafficSource as TrafficSourceDbModel  # Отложенный импорт
        return [cls.from_db_instance(role) for role in await TrafficSourceDbModel.get_all()]

    @classmethod
    def from_db_instance(cls, traffic_source_db_instance) -> 'TrafficSource':
        return cls(traffic_source_db_instance)

    @classmethod
    async def get_by_id(cls, role_id: int) -> Union['TrafficSource', None]:
        from .models.traffic_source import TrafficSource as TrafficSourceDbModel  # Отложенный импорт
        return cls.from_db_instance(await TrafficSourceDbModel.get_by_id(role_id))

    @property
    def id(self) -> int:
        return self._traffic_source_db_instance.id

    @property
    def name(self) -> str:
        return self._traffic_source_db_instance.name

    @property
    def description(self) -> str:
        return self._traffic_source_db_instance.description

    async def delete(self):
        await self._traffic_source_db_instance.delete()

    async def set_name(self, name: str):
        await self._traffic_source_db_instance.set_name(name)

    async def set_description(self, description: str):
        await self._traffic_source_db_instance.set_description(description)

    def __str__(self):
        return f"TrafficSource(id={self.id}, name='{self.name}')"

    def __repr__(self):
        return self.__str__()
