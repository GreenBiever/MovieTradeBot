from dataclasses import dataclass


@dataclass
class UserStatus:
    id: int


class UserStatuses:
    NOT_REGISTERED = WAITING_REQUEST = UserStatus(0)
    REQUEST_PENDING = UserStatus(1)
    ACTIVE = UserStatus(2)
    BLOCKED = RESTRICTED = UserStatus(3)

    ALL = [NOT_REGISTERED, REQUEST_PENDING, ACTIVE, BLOCKED]

    @classmethod
    def from_id(cls, status_id: int) -> 'UserStatus':
        for cls_attr_name in vars(cls):
            if type((status_obj := getattr(cls, cls_attr_name))) == UserStatus and status_obj.id == status_id:
                return status_obj
