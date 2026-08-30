from datetime import datetime
from typing import Optional

from pydantic import EmailStr, BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO
from src.modules.students.models_dto import UpdateStudentDTO
from src.modules.teachers.models_dto import UpdateTeacherDTO
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


class RegisterUserByAdminRequestDTO(RegisterUserRequestDTO):
    password_for_admin: str


class UpdateUserAccountDTO(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateUserDataRequestDTO(BaseModel):
    # Profile fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    description: Optional[str] = None  # applies to teacher only

    # User account fields
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

    def to_user_account_dto(self) -> UpdateUserAccountDTO:
        data = self.model_dump(exclude_unset=True)
        return UpdateUserAccountDTO(**{k: v for k, v in data.items() if k in UpdateUserAccountDTO.model_fields})

    def to_teacher_dto(self) -> UpdateTeacherDTO:
        data = self.model_dump(exclude_unset=True)
        return UpdateTeacherDTO(**{k: v for k, v in data.items() if k in UpdateTeacherDTO.model_fields})

    def to_student_dto(self) -> UpdateStudentDTO:
        data = self.model_dump(exclude_unset=True)
        return UpdateStudentDTO(**{k: v for k, v in data.items() if k in UpdateStudentDTO.model_fields})


class CreateUserDTO(BaseModel):
    email: str
    username: str
    hashed_password: str
    role: UserRole
