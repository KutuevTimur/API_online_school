from typing import List, Tuple
from sqlalchemy.sql.elements import ColumnElement

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.users.models import User, UserRole
from src.modules.users.models_dto import CreateUserDTO


class UsersRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=User)

    async def add_user(
        self,
        data: CreateUserDTO,
    ) -> User:
        return self.add(data)

    async def lock_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id).options(selectinload(User.teacher), selectinload(User.student)).with_for_update().execution_options(populate_existing=True))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        result_db = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.teacher),
                selectinload(User.student),
            )
        )
        return result_db.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        result_db = await self.session.execute(
            select(User)
            .where(
                User.username == username
            )
        )
        return result_db.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result_db = await self.session.execute(select(User).where(User.email == email))
        return result_db.scalar_one_or_none()

    async def get_users_by_role(
        self,
        role: UserRole,
        limit: int = 100,
        offset: int = 0,
        access_scope=None,
        q: str | None = None,
        school_grade: int | None = None,
        sort: str = "recent",
        teacher_user_id: int | None = None,
        attention: str | None = None,
    ) -> Tuple[int, List[User]]:
        """Apply search and permission scope before snapshot count and pagination."""
        from src.modules.base.list_query import snapshot_page
        stmt = select(User).where(User.role == role)
        if access_scope is not None:
            stmt = stmt.where(access_scope)
        if school_grade is not None:
            from src.modules.students.models import Student
            stmt = stmt.where(User.student.has(Student.school_grade == school_grade))
        if q is not None:
            stmt = stmt.where(self.search_scope(q))
        from sqlalchemy import func
        from src.modules.teacher_planning.repository import attention_counts
        counts = attention_counts(teacher_user_id) if teacher_user_id else None
        def missing(u, field):
            return func.coalesce(select(counts.c[field]).where(counts.c.student_user_id == u.id).correlate(u).scalar_subquery(), 0)
        if counts is not None and attention in ('homework', 'lecture'):
            stmt = stmt.where(missing(User, 'missing_' + attention) > 0)
        from src.modules.students.models import Student
        from src.modules.teachers.models import Teacher
        from src.modules.teacher_students.models import TeacherStudent
        def profile_value(u, field):
            return select(field).where(Student.user_id == u.id).correlate(u).scalar_subquery()
        def recent(u):
            if teacher_user_id is None:
                return u.created_at.desc()
            return (select(TeacherStudent.started_at).join(Student, Student.id == TeacherStudent.student_id)
                    .join(Teacher, Teacher.id == TeacherStudent.teacher_id)
                    .where(Student.user_id == u.id, Teacher.user_id == teacher_user_id,
                           TeacherStudent.ended_at.is_(None)).correlate(u).scalar_subquery().desc().nulls_last())
        ordering = (recent, lambda u: u.id.desc()) if role == UserRole.STUDENT else (lambda u: u.id.desc(),)
        if sort == "attention" and counts is not None:
            ordering = (lambda u: (missing(u, "missing_homework") + missing(u, "missing_lecture")).desc(), lambda u: u.id.asc())
        elif sort in {"grade_asc", "grade_desc"}:
            ordering = (lambda u: (profile_value(u, Student.school_grade).asc() if sort == "grade_asc"
                                  else profile_value(u, Student.school_grade).desc()).nulls_last(), lambda u: u.id.asc())
        elif sort == "name":
            ordering = (lambda u: func.lower(profile_value(u, Student.first_name)).asc().nulls_last(),
                        lambda u: func.lower(profile_value(u, Student.last_name)).asc().nulls_last(), lambda u: u.id.asc())
        users, total = await snapshot_page(self.session, User, stmt,
            ordering, limit, offset,
            (lambda u: selectinload(u.teacher), lambda u: selectinload(u.student)))
        return total, users

    async def update_user(
        self,
        user_id: int,
        values: dict,
    ) -> User | None:
        result_db = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**values)
            .returning(User)
        )
        return result_db.scalar_one_or_none()


    @staticmethod
    def search_scope(q: str) -> "ColumnElement[bool]":
        from sqlalchemy import or_
        from src.modules.teachers.models import Teacher
        from src.modules.students.models import Student
        pattern = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        def matches(model):
            return or_(model.first_name.ilike(pattern, escape="\\"),
                       model.last_name.ilike(pattern, escape="\\"),
                       (model.first_name + " " + model.last_name).ilike(pattern, escape="\\"),
                       (model.last_name + " " + model.first_name).ilike(pattern, escape="\\"))
        return or_(User.username.ilike(pattern, escape="\\"),
                   User.teacher.has(matches(Teacher)), User.student.has(matches(Student)))

    async def admin_page(self, role: UserRole | None, is_active: bool | None,
                         is_activated: bool | None, q: str | None,
                         limit: int, offset: int) -> tuple[list[User], int]:
        from src.modules.base.list_query import snapshot_page
        stmt = select(User)
        for field, value in ((User.role, role), (User.is_active, is_active),
                             (User.is_activated, is_activated)):
            if value is not None:
                stmt = stmt.where(field == value)
        if q is not None:
            stmt = stmt.where(self.search_scope(q))
        return await snapshot_page(self.session, User, stmt, (lambda u: u.id.desc(),),
            limit, offset, (lambda u: selectinload(u.teacher), lambda u: selectinload(u.student)))
