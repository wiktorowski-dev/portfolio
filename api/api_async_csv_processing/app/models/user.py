from sqlalchemy import Column, String
from pydantic import BaseModel, EmailStr, model_validator, field_validator

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)



class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one number.")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in value):
            raise ValueError("Password must contain at least one special character.")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
