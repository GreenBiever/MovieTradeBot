from .user import User
from users.user.pool import UserPool


def get_user_pool() -> UserPool:
    return UserPool()
