from pydantic import BaseModel, EmailStr, Field


class BootstrapInput(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
