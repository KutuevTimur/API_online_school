from fastapi import APIRouter, Depends
from starlette import status

from src.models.auth.depends import get_current_user
from src.models.users.models_dto import UserResponse

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(user = Depends(get_current_user)):
    return user


