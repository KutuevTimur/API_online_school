from src.modules.handlers_files.avatar_transaction import atomic_avatar_upload, retire_avatar
from src.modules.check_permission.service import ObjectPermissionService
import uuid
from pathlib import Path
from typing import Tuple, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.account_invitations.models_dto import InvitationUserResponse

from fastapi import UploadFile
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NotFoundData
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.students.models_dto import CreateStudentDTO, UpdateStudentDTO, StudentsDTO
from src.modules.students.models import Student
from src.modules.students.repository import StudentRepository
from src.modules.students.service import StudentService
from src.modules.teachers.repository import TeacherRepository
from src.modules.teachers.service import TeacherService
from src.modules.teachers.models_dto import CreateTeacherDTO, UpdateTeacherDTO, TeachersDTO
from src.modules.users.exception import UserAlreadyExit, InvalidRole, AvatarNotFound
from src.modules.users.models import User, UserRole
from src.modules.users.models_dto import (
    UserDTO,
    MinimalProfileResponseDTO,
    UpdateSchoolGradeRequestDTO,
    RegisterUserRequestDTO,
    CreateUserDTO,
    UserAvatarResponseDTO,
    UpdateUserDataRequestDTO,
    PublicProfileResponseDTO,
    AdminUserResponseDTO,
)
from src.modules.users.repository import UsersRepository
from src.modules.refresh_tokens.repository import RefreshTokenRepository


class UsersService:

    def __init__(
        self,
        users_repo: UsersRepository,
        teacher_repo: TeacherRepository,
        teacher_service: TeacherService,
        student_repo: StudentRepository,
        student_service: StudentService,
        cr_context: CryptContext,
        path_builder: PathBuilder,
        handler_images: HandlerImages,
        compression_images: CompressionImages,
        session_db: AsyncSession,
    ):
        self.users_repo = users_repo
        self.teacher_repo = teacher_repo
        self.teacher_service = teacher_service
        self.student_repo = student_repo
        self.student_service = student_service
        self.cr_context = cr_context
        self.path_builder = path_builder
        self.handler_images = handler_images
        self.compression_images = compression_images
        self.session_db = session_db

    def _get_hash_password(self, password: str) -> str:
        """Преобразует пароль в хеш
        :return: хэш пароля"""
        return self.cr_context.hash(password)

    async def _create_avatar(self, user_id: int, avatar: UploadFile) -> str:
        path = await self.handler_images.create_avatar()
        await self.handler_images.convert_to_webp(avatar, path)
        return str(path)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Проверяет, совпадает ли пароль с хешем
        :param plain_password: простой пароль (qwerty)
        :param hashed_password: хэш пароля (gfdjkjvzvxccxa)
        :return: результат совпадения
        """
        return self.cr_context.verify(plain_password, hashed_password)

    async def get_user_by_username(self, username: str) -> UserDTO | None:
        result = await self.users_repo.get_user_by_username(username)
        return UserDTO.model_validate(result) if result else None

    async def get_user_by_id(self, user_id: int) -> UserDTO | None:
        result = await self.users_repo.get_user_by_id(user_id)
        return UserDTO.model_validate(result) if result else None

    async def get_user_by_email(self, email: str) -> UserDTO | None:
        result = await self.users_repo.get_user_by_email(email)
        return UserDTO.model_validate(result) if result else None

    async def stage_create_inactive_account(
        self, new_user: RegisterUserRequestDTO,
    ) -> tuple[User, Student | None]:
        """Commit-free account/profile stage; caller validates rights and prelocks FKs."""
        hashed_password = self._get_hash_password(uuid.uuid4().hex)
        student = None
        user_orm = await self.users_repo.add_user(
            data=CreateUserDTO(
                email=new_user.email,
                username=new_user.username,
                hashed_password=hashed_password,
                role=new_user.role,
                is_activated=False,
            )
        )

        await self.session_db.flush()

        if new_user.role == UserRole.TEACHER:
            await self.teacher_repo.add_teacher(
                CreateTeacherDTO(
                    user_id=user_orm.id,
                    first_name=new_user.first_name,
                    last_name=new_user.last_name,
                    middle_name=new_user.middle_name,
                    description=new_user.description,
                )
            )
        elif new_user.role == UserRole.STUDENT:
            student = await self.student_repo.add_student(
                CreateStudentDTO(
                    user_id=user_orm.id,
                    first_name=new_user.first_name,
                    last_name=new_user.last_name,
                    middle_name=new_user.middle_name,
                    school_grade=new_user.school_grade,
                )
            )
        else:
            raise InvalidRole()
        return user_orm, student

    async def create_user(
        self,
        new_user: RegisterUserRequestDTO,
        actor: UserDTO,
    ) -> "InvitationUserResponse":
        """
        Создает нового пользователя (учителя или ученика).
        :raises UserAlreadyExit: Если пользователь с таким email/username уже существует.
        :raises InvalidRole: Если роль недопустима.
        """
        from src.modules.check_permission.exception import PermissionErrorService
        from src.modules.teacher_students.repository import TeacherStudentRepository
        if actor.role not in {UserRole.ADMIN, UserRole.TEACHER} or new_user.role == UserRole.ADMIN:
            raise PermissionErrorService()
        if actor.role == UserRole.TEACHER and new_user.role != UserRole.STUDENT:
            raise PermissionErrorService()
        if actor.role != UserRole.TEACHER and new_user.lesson_price_kopecks is not None:
            raise PermissionErrorService()
        teacher = None
        if actor.role == UserRole.TEACHER:
            teacher = await self.teacher_repo.get_teacher_by_user_id(actor.id)
            if teacher is None:
                raise PermissionErrorService()
        if new_user.email and await self.get_user_by_email(new_user.email):
            raise UserAlreadyExit()

        try:
            user_orm, student = await self.stage_create_inactive_account(new_user)

            if teacher is not None:
                await self.session_db.flush()
                link = await TeacherStudentRepository(self.session_db).link(teacher.id, student.id)
                link.lesson_price_kopecks = new_user.lesson_price_kopecks
            from src.modules.account_invitations.service import InvitationService
            invitation = await InvitationService(self).stage_issue(user_orm, "invite", actor)
            from src.modules.audit_events.service import AuditEventsService
            AuditEventsService(self.session_db).stage(actor.id, "account_create", "user", user_orm.id)
            await self.session_db.commit()
        except Exception as e:
            await self.session_db.rollback()
            if 'email' in str(e).lower() or 'duplicate key' in str(e).lower():
                raise UserAlreadyExit()
            else:
                raise

        from src.modules.account_invitations.models_dto import InvitationUserResponse
        from src.modules.users.models_dto import UserResponse
        return InvitationUserResponse(
            **UserResponse.model_validate(user_orm).model_dump(), **invitation.model_dump()
        )

    @atomic_avatar_upload
    async def update_avatar(self, user_id: int, avatar: UploadFile, actor: UserDTO) -> UserAvatarResponseDTO:
        await ObjectPermissionService(self.session_db).require(actor.id, "profile", user_id, write=True)
        user = await self.users_repo.lock_user(user_id)
        if not user:
            raise NotFoundData()
        profile = user.student if user.role == UserRole.STUDENT else user.teacher
        if profile is None:
            raise InvalidRole()
        old_path = profile.avatar_path
        avatar_path = await self._create_avatar(user_id, avatar)
        repo = self.student_repo if user.role == UserRole.STUDENT else self.teacher_repo
        if user.role == UserRole.STUDENT:
            await repo.update_student_by_user_id(user_id, {"avatar_path": avatar_path})
        else:
            await repo.update_teacher_by_user_id(user_id, {"avatar_path": avatar_path})
        retire_avatar(self.session_db, old_path)
        await self._audit_profile(actor, user_id, "avatar_update")
        await self.session_db.commit()
        self.handler_images.upload_committed = True
        return UserAvatarResponseDTO(avatar_path=f"/users/{user_id}/avatar")

    async def update_user(
        self,
        user_id: int,
        data: UpdateUserDataRequestDTO,
        actor: UserDTO,
    ) -> TeachersDTO | StudentsDTO:
        """
        Обновляет данные профиля пользователя (учителя или ученика) и аккаунта по user_id.
        :param user_id: ID пользователя
        :param data: Данные для обновления
        :return: TeachersDTO или StudentsDTO
        :raises NotFoundData: Если пользователь не найден
        :raises UserAlreadyExit: Если email или username уже заняты другим пользователем
        :raises InvalidRole: Если роль пользователя неизвестна
        """
        await ObjectPermissionService(self.session_db).require(actor.id, "profile", user_id, write=True)
        user = await self.users_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundData()

        # Обновление данных аккаунта (таблица User)
        user_account_dto = data.to_user_account_dto()
        user_values = {k: v for k, v in user_account_dto.model_dump(exclude_unset=True).items()
                       if v is not None or k == "email"}

        if user_values:
            if user_account_dto.email:
                existing_by_email = await self.users_repo.get_user_by_email(user_account_dto.email)
                if existing_by_email and existing_by_email.id != user_id:
                    raise UserAlreadyExit()
            if user_account_dto.username:
                existing_by_username = await self.users_repo.get_user_by_username(user_account_dto.username)
                if existing_by_username and existing_by_username.id != user_id:
                    raise UserAlreadyExit()

            await self.users_repo.update_user(user_id=user_id, values=user_values)

        # Обновление данных профиля (таблицы Teacher / Student)
        if user.role == UserRole.TEACHER:
            teacher_dto = data.to_teacher_dto()
            profile_values = teacher_dto.model_dump(exclude_unset=True, exclude_none=True)
            if profile_values:
                teacher = await self.teacher_repo.update_teacher_by_user_id(
                    user_id=user_id,
                    values=profile_values,
                )
            else:
                teacher = await self.teacher_repo.get_teacher_by_user_id(user_id=user_id)

            if not teacher:
                raise NotFoundData()
            await self._audit_profile(actor, user_id, "profile_update")
            await self.session_db.commit()
            await self.session_db.refresh(teacher)
            return TeachersDTO.model_validate(teacher)

        elif user.role == UserRole.STUDENT:
            student_dto = data.to_student_dto()
            profile_values = student_dto.model_dump(exclude_unset=True, exclude_none=True)
            if profile_values:
                student = await self.student_repo.update_student_by_user_id(
                    user_id=user_id,
                    values=profile_values,
                )
            else:
                student = await self.student_repo.get_student_by_user_id(user_id=user_id)

            if not student:
                raise NotFoundData()
            await self._audit_profile(actor, user_id, "profile_update")
            await self.session_db.commit()
            await self.session_db.refresh(student)
            return StudentsDTO.model_validate(student)

        else:
            raise InvalidRole()

    async def change_password(
        self,
        user_id: int,
        new_password: str,
        current_password: str | None = None,
    ) -> UserDTO:
        """
        Изменяет пароль пользователя по user_id.
        :param user_id: ID пользователя
        :param new_password: Новый пароль
        :return: UserDTO обновленного пользователя
        :raises NotFoundData: Если пользователь не найден
        """
        try:
            user = await self.users_repo.lock_user(user_id)
            if not user:
                raise NotFoundData()

            from src.modules.auth.exception import InvalidCredentials, require_active_user
            require_active_user(user)
            if current_password is None or not self.verify_password(current_password, user.hashed_password):
                raise InvalidCredentials()
            hashed_password = self._get_hash_password(new_password)
            updated_user = await self.users_repo.update_user(
                user_id=user_id,
                values={"hashed_password": hashed_password, "auth_version": user.auth_version + 1},
            )
            if not updated_user:
                raise NotFoundData()

            await RefreshTokenRepository(self.session_db).revoke_user(user_id)
            from src.modules.account_invitations.repository import InvitationRepository
            await InvitationRepository(self.session_db).invalidate(user_id, "reset")
            await self.session_db.commit()
            await self.session_db.refresh(updated_user)
            return UserDTO.model_validate(updated_user)
        except Exception:
            await self.session_db.rollback()
            raise

    async def _audit_profile(self, actor: UserDTO, target_id: int, action: str) -> None:
        if actor.role == UserRole.ADMIN:
            from src.modules.account_invitations.models import AccountAudit
            self.session_db.add(AccountAudit(actor_user_id=actor.id, target_user_id=target_id,
                                            action=action, correlation_id=uuid.uuid4().hex))

    def _profile_response(self, user, actor):
        from src.modules.users.models_dto import MinimalProfileResponseDTO
        if actor.role == UserRole.ADMIN or actor.id == user.id:
            return PublicProfileResponseDTO.model_validate(user)
        profile = user.student if user.role == UserRole.STUDENT else user.teacher
        if profile is None:
            raise NotFoundData()
        return MinimalProfileResponseDTO(user_id=user.id, username=user.username,
            school_grade=profile.school_grade if user.role == UserRole.STUDENT else None,
            first_name=profile.first_name, last_name=profile.last_name,
            avatar_path=f"/users/{user.id}/avatar" if profile.avatar_path else None)

    async def get_students(self, actor: UserDTO, limit: int = 100, offset: int = 0, q: str | None = None, school_grade: int | None = None, sort="recent", attention=None):
        from src.modules.check_permission.exception import PermissionErrorService
        if actor.role not in {UserRole.ADMIN, UserRole.TEACHER}:
            raise PermissionErrorService()
        return await self._list_profiles(actor, UserRole.STUDENT, limit, offset, q, school_grade, sort, attention)

    async def get_teachers(self, actor: UserDTO, limit: int = 100, offset: int = 0):
        return await self._list_profiles(actor, UserRole.TEACHER, limit, offset)

    async def _list_profiles(self, actor, role, limit, offset, q=None, school_grade=None, sort="recent", attention=None):
        from src.modules.check_permission.repository import profile_scope
        total, users = await self.users_repo.get_users_by_role(
            role, limit, offset, access_scope=profile_scope(actor.id, actor.role), q=q, school_grade=school_grade, sort=sort, teacher_user_id=actor.id if actor.role == UserRole.TEACHER else None, attention=attention)
        items = [self._profile_response(user, actor) for user in users]
        if actor.role == UserRole.TEACHER and role == UserRole.STUDENT:
            from src.modules.teacher_planning.repository import TeacherPlanningRepository
            rows = await TeacherPlanningRepository(self.session_db).student_attention(actor.id, [u.id for u in users])
            from src.modules.users.models_dto import TeacherStudentProfileResponseDTO
            items = [TeacherStudentProfileResponseDTO(**item.model_dump(),
                missing_homework=rows[item.user_id].missing_homework if item.user_id in rows else 0,
                missing_lecture=rows[item.user_id].missing_lecture if item.user_id in rows else 0) for item in items]
        return total, items

    async def get_public_profile(self, user_id: int, actor: UserDTO):
        await ObjectPermissionService(self.session_db).require(actor.id, "profile", user_id)
        user = await self.users_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundData()
        return self._profile_response(user, actor)

    async def avatar_file(self, actor: UserDTO, user_id: int) -> Path:
        await ObjectPermissionService(self.session_db).require(actor.id, "profile", user_id)
        user = await self.users_repo.get_user_by_id(user_id)
        profile = user.student if user.role == UserRole.STUDENT else user.teacher
        path = Path(profile.avatar_path) if profile and profile.avatar_path else None
        if path is None:
            raise NotFoundData()
        return path

    @atomic_avatar_upload
    async def remove_avatar(self, actor: UserDTO, user_id: int) -> None:
        await ObjectPermissionService(self.session_db).require(actor.id, "profile", user_id, write=True)
        # Remove the pointer before removing the file so responses cannot expose stale paths.
        user = await self.users_repo.lock_user(user_id)
        profile = user.student if user.role == UserRole.STUDENT else user.teacher
        if not profile or not profile.avatar_path:
            raise AvatarNotFound()
        retire_avatar(self.session_db, profile.avatar_path)
        if user.role == UserRole.STUDENT:
            await self.student_repo.update_student_by_user_id(user_id, {"avatar_path": None})
        elif user.role == UserRole.TEACHER:
            await self.teacher_repo.update_teacher_by_user_id(user_id, {"avatar_path": None})
        else:
            raise InvalidRole()
        await self._audit_profile(actor, user_id, "avatar_delete")
        await self.session_db.commit()
        self.handler_images.upload_committed = True

    async def update_account_status(self, actor: UserDTO, user_id: int, is_active: bool):
        from src.modules.check_permission.exception import PermissionErrorService
        from src.modules.users.models_dto import UserResponse
        if actor.role != UserRole.ADMIN:
            raise PermissionErrorService()
        user = await self.users_repo.lock_user(user_id)
        if user is None:
            raise NotFoundData()
        try:
            await self.users_repo.update_user(user_id, {"is_active": is_active, "auth_version": user.auth_version + 1})
            await RefreshTokenRepository(self.session_db).revoke_user(user_id)
            await self._audit_profile(actor, user_id, "account_status")
            await self.session_db.commit()
            return UserResponse.model_validate(user)
        except Exception:
            await self.session_db.rollback()
            raise


    @staticmethod
    def _require_admin(actor: UserDTO) -> None:
        from src.modules.check_permission.exception import PermissionErrorService
        if actor.role != UserRole.ADMIN:
            raise PermissionErrorService()

    @staticmethod
    def _admin_profile(user: User) -> AdminUserResponseDTO:
        from src.modules.users.models_dto import AdminUserResponseDTO
        profile = user.student if user.role == UserRole.STUDENT else user.teacher
        return AdminUserResponseDTO(user_id=user.id, username=user.username,
            email=user.email, role=user.role, is_active=user.is_active,
            is_activated=user.is_activated, created_at=user.created_at,
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
            middle_name=profile.middle_name if profile else None,
            description=getattr(profile, "description", None),
            avatar_path=f"/users/{user.id}/avatar" if profile and profile.avatar_path else None)

    async def admin_users(self, actor: UserDTO, role: UserRole | None,
                          is_active: bool | None, is_activated: bool | None,
                          q: str | None, limit: int, offset: int) -> tuple[list[AdminUserResponseDTO], int]:
        self._require_admin(actor)
        users, total = await self.users_repo.admin_page(role, is_active, is_activated, q, limit, offset)
        return [self._admin_profile(user) for user in users], total

    async def admin_user(self, actor: UserDTO, user_id: int) -> AdminUserResponseDTO:
        self._require_admin(actor)
        user = await self.users_repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundData()
        return self._admin_profile(user)

    async def update_school_grade(self, actor: UserDTO, user_id: int, data: UpdateSchoolGradeRequestDTO) -> PublicProfileResponseDTO | MinimalProfileResponseDTO:
        """Narrow shared-field permission; never grants teacher general profile writes."""
        from src.modules.check_permission.exception import PermissionErrorService
        from src.modules.base.exception import StaleUpdate
        try:
            if actor.role == UserRole.TEACHER:
                await ObjectPermissionService(self.session_db).require_link(actor.id, user_id)
                from src.modules.teacher_students.repository import TeacherStudentRepository
                teacher = await self.teacher_repo.get_teacher_by_user_id(actor.id)
                student = await self.student_repo.get_student_by_user_id(user_id)
                link = await TeacherStudentRepository(self.session_db).previous_link(teacher.id, student.id)
                if link is None or link.ended_at is not None:
                    raise PermissionErrorService()
            elif actor.role != UserRole.ADMIN and actor.id != user_id:
                raise PermissionErrorService()
            user = await self.users_repo.lock_user(user_id)
            if user is None or user.role != UserRole.STUDENT or user.student is None:
                raise NotFoundData()
            # Lock the profile as well: other teachers share this value.
            student = await self.student_repo.lock_by_user_id(user_id)
            if student.school_grade != data.expected_school_grade:
                raise StaleUpdate()
            await self.student_repo.update_student_by_user_id(user_id, {"school_grade": data.school_grade})
            from src.modules.audit_events.service import AuditEventsService
            AuditEventsService(self.session_db).stage(actor.id, "student_grade_update", "user", user_id)
            await self.session_db.commit()
            return await self.get_public_profile(user_id, actor)
        except Exception:
            await self.session_db.rollback()
            raise
