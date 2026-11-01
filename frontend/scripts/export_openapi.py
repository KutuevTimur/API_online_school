"""Export source schema only: no configuration, engine, lifespan or DB I/O."""
import json
import sys
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.core.config import Config
from src.modules.api.app import init_fastapi_app

# Factory stores this sentinel; schema generation never accesses runtime config.
app = init_fastapi_app(config=cast(Config, object()))
print(json.dumps(app.openapi(), ensure_ascii=False, sort_keys=True))
