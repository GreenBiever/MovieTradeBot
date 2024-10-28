from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .user import User


class UserException(BaseException):

    def __init__(self, user: 'User'):
        self.user = user


class TagChangeNotAllowed(UserException):
    pass