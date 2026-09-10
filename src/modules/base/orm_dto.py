from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, ConfigDict


class ORMDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


T = TypeVar("T")

class PaginationResponseDTO(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: Optional[int] = None
    offset: Optional[int] = None
