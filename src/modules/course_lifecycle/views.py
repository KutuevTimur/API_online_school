from fastapi import APIRouter, Depends, Query, Response
from src.modules.check_permission.depends import get_current_admin_user
from src.modules.users.models_dto import UserDTO
from src.modules.courses.models_dto import CoursesResponseDTO
from src.modules.lessons.models_dto import LessonResponseDTO
from src.modules.course_lifecycle.models_dto import PurgeCourseRequest, HistoryAccessRequest, CleanupResponse, PurgeResponse
from src.modules.course_lifecycle.depends import get_lifecycle_service
from src.modules.course_lifecycle.service import LifecycleService

router = APIRouter(tags=['Course lifecycle'])


@router.post('/courses/{course_id}/restore', response_model=CoursesResponseDTO, status_code=200)
async def restore_course(course_id: int, actor: UserDTO = Depends(get_current_admin_user),
                         service: LifecycleService = Depends(get_lifecycle_service)):
    return await service.restore(actor.id, 'course', course_id)


@router.post('/lessons/{lesson_id}/restore', response_model=LessonResponseDTO, status_code=200)
async def restore_lesson(lesson_id: int, actor: UserDTO = Depends(get_current_admin_user),
                         service: LifecycleService = Depends(get_lifecycle_service)):
    return await service.restore(actor.id, 'lesson', lesson_id)


@router.patch('/courses/{course_id}/students/{user_id}/history-access', status_code=204)
async def history_access(course_id: int, user_id: int, data: HistoryAccessRequest,
                         actor: UserDTO = Depends(get_current_admin_user),
                         service: LifecycleService = Depends(get_lifecycle_service)):
    await service.history_access(actor.id, course_id, user_id, data.revoked)
    return Response(status_code=204)


@router.post('/courses/{course_id}/purge', response_model=PurgeResponse, status_code=200)
async def purge_course(course_id: int, data: PurgeCourseRequest,
                       actor: UserDTO = Depends(get_current_admin_user),
                       service: LifecycleService = Depends(get_lifecycle_service)):
    return await service.purge(actor.id, course_id, data)


@router.post('/admin/file-deletions/retry', response_model=CleanupResponse, status_code=200)
async def retry_cleanup(limit: int = Query(100, ge=1, le=1000),
                        actor: UserDTO = Depends(get_current_admin_user),
                        service: LifecycleService = Depends(get_lifecycle_service)):
    return await service.cleanup(actor.id, limit)
