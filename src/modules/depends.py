from fastapi import Request

from src.core.config import Config


def get_config(request: Request) -> Config:
    return request.app.state.config