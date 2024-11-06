from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from databases.models import User  # импорт вашего класса User  # предположительно, модель Profit
from users.role.default import UserRoles
