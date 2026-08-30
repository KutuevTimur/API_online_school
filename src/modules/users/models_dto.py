from datetime import datetime
from typing import Optional

from pydantic import EmailStr, BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO
from src.modules.users.models import UserRole


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


class UserAvatarResponseDTO(BaseModel):
    avatar_path: str

    model_config = ConfigDict(from_attributes=True)


class RegisterUserRequestDTO(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole

    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CreateUserDTO(BaseModel):
    email: str
    username: str
    hashed_password: str
    role: UserRole
