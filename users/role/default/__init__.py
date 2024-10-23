from typing import Type


class UserRoleBase:
    id: int = -1
    name: str = ''


class AbstractUserRoleBase:
    """
    Abstract role class defines that user has some role that can not be checked from simple role id compare
    """

    name: str = ''

    # async def check(self, **params) -> bool:
    #     pass


UserRoleT = Type[UserRoleBase]
AbstractUserRoleT = Type[AbstractUserRoleBase]
# TypeUserRole = Type[UserRoleBase] | Type[AbstractUserRoleBase]


class UserRoles:

    class Worker(UserRoleBase):
        id = 1
        name = '🥷🏿 Воркер'

    class Cashier(UserRoleBase):
        id = 2
        name = '💳 Вбивер'

    class Admin(UserRoleBase):
        id = 3
        name = '🤴 Админ'

    class Coder(UserRoleBase):
        id = 4
        name = '👨‍💻 Прогер'

    class Support(UserRoleBase):
        id = 5
        name = '📣 Саппорт'

    class Caller(UserRoleBase):
        id = 6
        name = '📞 Звонер'

    class Mentor(AbstractUserRoleBase):
        name = '👨‍🎓 Ментор'

    class SeniorMentor(AbstractUserRoleBase):
        name = '👨‍🎓 Старший ментор'

    SUPER_ROLE_ID_LIST = [Admin.id, Coder.id]
    ID_LIST = [Worker.id, Cashier.id, Admin.id, Coder.id, Support.id, Caller.id]
