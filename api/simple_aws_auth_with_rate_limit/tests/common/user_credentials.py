from dataclasses import dataclass


class UserMeta(type):
    @property
    def id(cls) -> str:
        return cls.username


@dataclass
class User(metaclass=UserMeta):
    username = 'user@example.com'
    email = 'user@example.com'
    password = 'NewPassword123!'

