from typing import Union, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func
from databases.models import UserCode as RefCodeORMModel
from .models.ref_code import RefCode as RefCodeDbModel
from .ref_code import RefCode



class RefCodePool:

    @classmethod
    async def get_by_name(cls, session: AsyncSession, *names: str, user_id: Optional[int] = None) -> Union[
        RefCode, List[RefCode], None]:
        query = select(RefCodeORMModel).where(RefCodeORMModel.name.in_(names))
        if user_id is not None:
            query = query.where(RefCodeORMModel.user_id == user_id)

        result = await session.execute(query)
        ref_codes_filtered = result.scalars().all()
        ref_code_list = cls._get_ref_code_instances_from_orm_obj_list(ref_codes_filtered)

        return ref_code_list[0] if len(names) == 1 else ref_code_list

    @classmethod
    async def get_by_id(cls, session: AsyncSession, *ids: int, user_id: Optional[int] = None) -> Union[
        RefCode, List[RefCode], None]:
        query = select(RefCodeORMModel).where(RefCodeORMModel.id.in_(ids))
        if user_id is not None:
            query = query.where(RefCodeORMModel.user_id == user_id)

        result = await session.execute(query)
        ref_codes_filtered = result.scalars().all()
        ref_code_list = cls._get_ref_code_instances_from_orm_obj_list(ref_codes_filtered)

        return ref_code_list[0] if len(ids) == 1 else ref_code_list

    @classmethod
    async def get_by_user_id(cls, session: AsyncSession, user_id: int) -> List[RefCode]:
        result = await session.execute(
            select(RefCodeORMModel).where(RefCodeORMModel.user_id == user_id)
        )
        ref_codes_filtered = result.scalars().all()
        return cls._get_ref_code_instances_from_orm_obj_list(ref_codes_filtered)

    @classmethod
    def _get_ref_code_instances_from_orm_obj_list(cls, ref_code_orm_obj_list: List[RefCodeORMModel]) -> List[RefCode]:
        return [cls._init_ref_code_instance(ref_code) for ref_code in ref_code_orm_obj_list]

    @classmethod
    def _init_ref_code_instance(cls, ref_code_orm_obj: RefCodeORMModel) -> RefCode:
        return RefCode.from_db_instance(RefCodeDbModel.from_db_instance(ref_code_orm_obj))
