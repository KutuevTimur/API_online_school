import logging
import random
import string
from datetime import datetime
from typing import Type, Any, Dict

from dateutil.parser import parse
from orjson import orjson
from pydantic import BaseModel

from src.core.database.database import Base


def _get_dict(obj: Any) -> Dict:
    if isinstance(obj, dict): return obj
    elif isinstance(obj, bytes): return orjson.loads(obj)
    elif isinstance(obj, BaseModel): return obj.model_dump()
    elif isinstance(obj, Base): return obj.to_dict()
    else: raise RuntimeError(f"невалидный формат у: {obj}")


def comparison_models(Expected: Type | dict, Actual: Type | dict, keys_not_checked: list = []):
    """Сравнивает две модели БД"""
    Expected = _get_dict(Expected)
    Actual = _get_dict(Actual)

    if not Actual:
        return False

    for key in Expected.keys():
        if not key in keys_not_checked:
            # если ожидаемый результат должен быть датой, и актуальный является не датой
            if isinstance(Expected[key], datetime) and not isinstance(Actual[key], datetime):
                assert Expected[key] == parse(Actual[key])
            elif isinstance(Expected[key], dict) and isinstance(Actual[key], dict):
                comparison_models(Expected[key], Actual[key])
            else:
                if not Expected[key] == Actual[key]:
                    logging.getLogger("comparison_models").info(f"ключ '{key}' не совпал")
                    return False

        return True


def random_string(length: int = 10) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))