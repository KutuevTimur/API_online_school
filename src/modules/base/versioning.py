from datetime import datetime
from src.modules.base.exception import StaleUpdate


def check_updated_at(expected: datetime | None, current: datetime) -> None:
    if expected is not None and expected != current:
        raise StaleUpdate("Object changed; reload before saving")
