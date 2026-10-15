from typing import Literal
from pydantic import BaseModel, Field, StrictInt


class StorageQuotaRequest(BaseModel):
    limit_bytes: StrictInt = Field(ge=20*1024*1024,le=1024*1024*1024*1024)


class CourseStorageUsage(BaseModel):
    course_id: int
    bytes: int


class StorageQuotaResponse(BaseModel):
    user_id: int
    limit_bytes: int
    used_bytes: int
    warning: Literal['near_limit','critical','full'] | None
    courses: list[CourseStorageUsage]
