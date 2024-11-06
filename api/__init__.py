from pydantic import BaseModel
from users.user import get_user_pool, User


class UserResolver(BaseModel):
    type: str
    from_value: str


class UserResolveHandler:

    def __init__(self, resolve_data: UserResolver | dict):
        self.resolve_data = resolve_data if isinstance(resolve_data, UserResolver) else UserResolver(**resolve_data)

    async def resolve(self) -> 'User':
        resolvers = {
            'user_code': get_user_pool().get_by_ref_code,
            'username': get_user_pool().get_by_username,
        }
        return await resolvers[self.resolve_data.type](self.resolve_data.from_value)
