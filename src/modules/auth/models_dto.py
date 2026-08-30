from typing import Optional
from pydantic import BaseModel, ConfigDict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class LogoutRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    success: bool


class ChangePasswordRequestDTO(BaseModel):
    new_password: str

    model_config = ConfigDict(from_attributes=True)
