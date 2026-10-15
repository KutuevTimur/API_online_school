from fastapi import APIRouter, Depends
from src.modules.auth.depends import get_current_user
from src.modules.check_permission.depends import get_current_admin_user
from src.modules.files.models_dto import StorageQuotaRequest, StorageQuotaResponse
from src.modules.files.service import StorageQuotaService
from src.modules.files.depends import get_storage_quota_service
from src.modules.users.models_dto import UserDTO

router=APIRouter(tags=['Storage'])


@router.get('/users/{user_id}/storage',response_model=StorageQuotaResponse,status_code=200)
async def storage_usage(user_id: int,actor: UserDTO=Depends(get_current_user),service: StorageQuotaService=Depends(get_storage_quota_service)):
    return await service.report_for(actor.id,actor.role,user_id)


@router.patch('/admin/users/{user_id}/storage-quota',response_model=StorageQuotaResponse,status_code=200)
async def storage_quota(user_id: int,data: StorageQuotaRequest,actor: UserDTO=Depends(get_current_admin_user),
                        service: StorageQuotaService=Depends(get_storage_quota_service)):
    return await service.change(actor.id,user_id,data.limit_bytes)
