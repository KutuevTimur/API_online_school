from pydantic import BaseModel, Field


class PurgeCourseRequest(BaseModel):
    confirm_course_id: int = Field(gt=0)
    confirm_name: str


class HistoryAccessRequest(BaseModel):
    revoked: bool


class CleanupResponse(BaseModel):
    completed: int
    failed: int


class PurgeResponse(BaseModel):
    course_id: int
    cleanup: CleanupResponse
