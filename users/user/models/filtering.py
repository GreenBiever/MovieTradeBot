from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from databases.models import User  # импорт вашего класса User
from databases.models import Profit  # предположительно, модель Profit
from users.role.default import UserRoles
async def get_inactive_user_filter_by_profits(
    session: AsyncSession,
    min_days_inactive: int,
    min_days_in_team: int = 60,
    worker_role_id: int = UserRoles.Worker.id  # ID роли Worker
):
    current_date = datetime.now()
    inactive_date_threshold = current_date - timedelta(days=min_days_inactive)
    join_date_threshold = current_date - timedelta(days=min_days_in_team)

    # Подзапрос для получения даты последней прибыли
    subquery_last_profit_date = (
        select(func.max(Profit.timestamp))
        .where(Profit.user == User.id)
        .correlate(User)
        .as_scalar()
    )

    # Основной запрос
    query = (
        select(User)
        .where(
            and_(
                or_(
                    subquery_last_profit_date.is_(None),
                    subquery_last_profit_date < inactive_date_threshold
                ),
                User.join_date <= join_date_threshold,
                User.role_id == worker_role_id
            )
        )
    )

    result = await session.execute(query)
    return result.scalars().all()
