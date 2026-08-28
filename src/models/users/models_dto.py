from datetime import datetime

from pydantic import EmailStr, BaseModel, ConfigDict

from src.models.base.orm_dto import ORMDTO
from src.models.users.models import UserRole


class UsersDTO(ORMDTO):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    hashed_password: str
    created_at: datetime


class UserResponse(ORMDTO):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    created_at: datetime


class RegisterUserRequestDTO(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class CreateUserDTO(BaseModel):
    email: str
    username: str
    hashed_password: str
    role: UserRole