from dataclasses import dataclass


@dataclass
class UserGroup:
    id: int
    name: str = None
    percent_bonus: float = None
    ref_code_limit: int = None


class UserGroups:
    NEWBIE = UserGroup(
        id=1,
        name='🐣 Новичок',
        percent_bonus=0.00,
        ref_code_limit=1
    )
    EXPERIENCED = UserGroup(
        id=2,
        name='👨‍🎓 Опытный',
        percent_bonus=0.05,
        ref_code_limit=2
    )
    TOP_WORKER = UserGroup(
        id=3,
        name='🎖 ТОП воркер',
        percent_bonus=0.1,
        ref_code_limit=5
    )

    @classmethod
    def from_id(cls, group_id: int) -> 'UserGroup':
        for cls_attr_name in vars(cls):
            if type((group_obj := getattr(cls, cls_attr_name))) == UserGroup and group_obj.id == group_id:
                return group_obj
