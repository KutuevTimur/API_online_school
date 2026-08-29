from fastapi import Request

from src.models.path_builder.service import PathBuilder


def get_path_builder(
    request: Request,
) -> PathBuilder:
    return PathBuilder(
        config=request.app.state.config,
    )