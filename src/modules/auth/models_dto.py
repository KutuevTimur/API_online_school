from src.modules.auth.password_dto import Password
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
    current_password: str
    new_password: Password

    model_config = ConfigDict(from_attributes=True)


class BrowserTokenResponse(BaseModel):
    access_token: str
    token_type: str
