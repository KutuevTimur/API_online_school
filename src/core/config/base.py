import os
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]


def init_env(*, test: bool = False) -> dict[str, str]:
    # Explicit source: test settings never inherit .env or ambient DB credentials.
    filename = ".env.test" if test or os.environ.get("MODE") == "TEST" else ".env"
    values = {k: v for k, v in dotenv_values(ROOT / filename).items() if v is not None}
    if filename == ".env":
        values.update(os.environ)
    return values
