from pathlib import Path
from src.core.config.config import Config


def create_config(*, test: bool = False, media_root: Path | None = None) -> Config:
    return Config(test=test, media_root=media_root)
