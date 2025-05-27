from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Literal, Optional, Any
import uuid
import re


class AccountSettings(BaseModel):
    newsletter_subscribed: bool = False

    class Config:
        extra = "forbid"


class AccountSettingsDB(AccountSettings):
    id: str = Field(default_factory=lambda: uuid.uuid4().__str__())
    user_id: str

    class Config:
        extra = "forbid"


class UserBase(BaseModel):
    email: EmailStr

    class Config:
        extra = "forbid"


class UserId(UserBase):
    id: str

    class Config:
        extra = "forbid"


class UserPassword(UserId):
    hashed_password: str

    class Config:
        extra = "forbid"


class UserCreate(UserBase):
    password: str
    newsletter_subscribed: bool

    class Config:
        extra = "forbid"

    @field_validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        #     raise ValueError('Password must contain at least one special character')
        return v


class User(UserBase):
    id: str
    account_settings: AccountSettingsDB

    class Config:
        extra = "forbid"


class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        extra = "forbid"


class TokenData(BaseModel):
    id: Optional[str] = None

    class Config:
        extra = "forbid"


class ConfirmForgotPasswordRequest(BaseModel):
    username: str
    confirmation_code: str
    password: str

    class Config:
        extra = "forbid"

    @field_validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        #     raise ValueError('Password must contain at least one special character')
        return v


class ChangePasswordRequest(BaseModel):
    token: str
    previous_password: str
    proposed_password: str

    class Config:
        extra = "forbid"
