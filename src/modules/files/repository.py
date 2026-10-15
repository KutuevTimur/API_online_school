from sqlalchemy import func, or_, select, union, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.files.models import FileAsset
from src.modules.users.models import User
from src.modules.students.models import Student
from src.modules.lectures.models import Lecture
from src.modules.homeworks.models import Homework
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile
from src.modules.lesson_students.models import LessonStudent
from src.modules.lessons.models import Lesson
from src.modules.base.exception import NotFoundData


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.files.models import FileAsset


class FileAssetsRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=FileAsset)

    async def ready(self, asset_id: int) -> FileAsset | None:
        return await self.session.scalar(select(FileAsset).where(
            FileAsset.id == asset_id, FileAsset.state == 'ready'))

    async def prune(self, asset_ids: set[int]) -> None:
        """Remove metadata only after the final domain FK has been removed."""
        from sqlalchemy import delete, exists, or_
        from src.modules.lectures.models import Lecture
        from src.modules.homeworks.models import Homework
        from src.modules.homework_submissions.models import HomeworkSubmissionFile
        references = [exists(select(model.id).where(or_(
            model.original_asset_id == FileAsset.id, model.download_asset_id == FileAsset.id)))
            for model in (Lecture, Homework, HomeworkSubmissionFile)]
        if asset_ids:
            await self.session.execute(delete(FileAsset).where(
                FileAsset.id.in_(asset_ids), ~or_(*references)).execution_options(synchronize_session=False))

    async def legacy_candidates(self, limit: int) -> list[tuple[type, int]]:
        from src.modules.lectures.models import Lecture
        from src.modules.homeworks.models import Homework
        from src.modules.homework_submissions.models import HomeworkSubmissionFile
        result = []
        for model in (Lecture, Homework, HomeworkSubmissionFile):
            query = select(model.id).where(
                (model.original_asset_id.is_(None) & model.original_file_path.is_not(None) & (model.original_file_path != '')) |
                (model.download_asset_id.is_(None) & model.pdf_file_path.is_not(None) & (model.pdf_file_path != ''))
            ).order_by(model.id).limit(max(0,limit-len(result)))
            result.extend((model,i) for i in (await self.session.scalars(query)).all())
            if len(result) >= limit:
                break
        return result

    async def lock_legacy(self, model: type, object_id: int):
        return await self.session.scalar(select(model).where(model.id == object_id)
            .with_for_update(skip_locked=True).execution_options(populate_existing=True))

    async def bind_legacy(self, model: type, object_id: int, values: dict) -> None:
        from sqlalchemy import update
        await self.session.execute(update(model).where(model.id==object_id).values(**values))

    async def owner_course(self, model: type, object_id: int) -> int:
        from src.modules.homeworks.models import Homework
        from src.modules.lectures.models import Lecture
        from src.modules.homework_submissions.models import HomeworkSubmissionFile, HomeworkSubmission
        from src.modules.lesson_students.models import LessonStudent
        from src.modules.lessons.models import Lesson
        if model is HomeworkSubmissionFile:
            stmt = select(Lesson.course_id).select_from(model).join(HomeworkSubmission,
                HomeworkSubmission.id==model.submission_id).join(Homework,Homework.id==HomeworkSubmission.homework_id)
            stmt = stmt.join(LessonStudent,LessonStudent.id==Homework.lesson_student_id)
        else:
            stmt = select(Lesson.course_id).select_from(model).join(LessonStudent,LessonStudent.id==model.lesson_student_id)
        return await self.session.scalar(stmt.join(Lesson,Lesson.id==LessonStudent.lesson_id).where(model.id==object_id))

    async def purged_courses(self) -> set[int]:
        from src.modules.course_lifecycle.models import LifecycleAudit
        return set((await self.session.scalars(select(LifecycleAudit.object_id).where(
            LifecycleAudit.object_type=='course',LifecycleAudit.action=='purge',LifecycleAudit.result=='success'))).all())


class StorageQuotaRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session,model=FileAsset)

    async def lock_limit(self, user_id: int) -> int:
        # NO KEY UPDATE serializes budgets without conflicting with uploader FKs.
        value=await self.session.scalar(select(User.file_quota_bytes).where(User.id==user_id)
            .with_for_update(key_share=True))
        if value is None:
            raise NotFoundData()
        return value

    def _assets(self,user_id: int):
        queries=[]
        for model in (Lecture,Homework,HomeworkSubmissionFile):
            for column in (model.original_asset_id,model.download_asset_id):
                stmt=select(column.label('asset_id'),Lesson.course_id.label('course_id')).select_from(model)
                if model is HomeworkSubmissionFile:
                    stmt=stmt.join(HomeworkSubmission,HomeworkSubmission.id==model.submission_id).join(
                        Homework,Homework.id==HomeworkSubmission.homework_id).join(LessonStudent,LessonStudent.id==Homework.lesson_student_id)
                else:
                    stmt=stmt.join(LessonStudent,LessonStudent.id==model.lesson_student_id)
                queries.append(stmt.join(Student,Student.id==LessonStudent.student_id).join(
                    Lesson,Lesson.id==LessonStudent.lesson_id).where(Student.user_id==user_id,column.is_not(None)))
        return union(*queries).subquery()

    async def usage(self,user_id: int,pending: set[int] | None=None) -> int:
        assets=self._assets(user_id)
        predicate=FileAsset.id.in_(select(assets.c.asset_id))
        if pending:
            predicate=or_(predicate,FileAsset.id.in_(pending))
        return int(await self.session.scalar(select(func.coalesce(func.sum(FileAsset.size),0)).where(predicate)) or 0)

    async def courses(self,user_id: int) -> list[dict[str,int]]:
        assets=self._assets(user_id)
        rows=(await self.session.execute(select(assets.c.course_id,func.sum(FileAsset.size)).join(
            FileAsset,FileAsset.id==assets.c.asset_id).group_by(assets.c.course_id).order_by(assets.c.course_id))).all()
        return [{'course_id':cid,'bytes':int(size)} for cid,size in rows]

    async def set_limit(self,user_id: int,limit: int) -> None:
        await self.session.execute(update(User).where(User.id==user_id).values(file_quota_bytes=limit))
