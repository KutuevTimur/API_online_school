from datetime import datetime
from typing import Optional

from pydantic import EmailStr, BaseModel, ConfigDict, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.students.models_dto import UpdateStudentDTO, StudentsResponseDTO
from src.modules.teachers.models_dto import UpdateTeacherDTO, TeachersResponseDTO
from src.modules.users.models import UserRole


class UserDTO(ORMDTO):
    id: int
    email: EmailStr | None = None
    username: str
    role: UserRole
    is_active: bool
    hashed_password: str
    is_activated: bool = True
    auth_version: int = 0
    created_at: datetime


class UserResponse(ORMDTO):
    id: int
    email: EmailStr | None = None
    username: str
    role: UserRole
    created_at: datetime


class PublicProfileResponseDTO(UserResponse):
    teacher: Optional[TeachersResponseDTO] = None
    student: Optional[StudentsResponseDTO] = None


class UserAvatarResponseDTO(BaseModel):
    avatar_path: str

    model_config = ConfigDict(from_attributes=True)


class RegisterUserRequestDTO(BaseModel):
    email: EmailStr | None = None
    username: str = Field(min_length=1, max_length=255)
    role: UserRole

    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RegisterUserByAdminRequestDTO(RegisterUserRequestDTO):
    password_for_admin: str | None = None


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
    model_config = ConfigDict(from_attributes=True, extra="forbid")

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
    email: str | None = None
    username: str
    hashed_password: str
    is_activated: bool = True
    auth_version: int = 0
    role: UserRole


class MinimalProfileResponseDTO(BaseModel):
    user_id: int
    username: str
    first_name: str
    last_name: str
    avatar_path: str | None = None


class AdminAccountStatusRequestDTO(BaseModel):
    is_active: bool
    model_config = ConfigDict(extra="forbid")
