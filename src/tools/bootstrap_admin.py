"""Interactive first-admin bootstrap. No password arguments or secret output."""
import asyncio
import getpass
from pathlib import Path
from tempfile import TemporaryDirectory
from src.core.config.test_guard import require_test_config
from passlib.context import CryptContext
from src.core.config import create_config
import src.modules.db_models  # noqa: F401


from src.modules.users.bootstrap_dto import BootstrapInput
from src.modules.users.bootstrap_service import bootstrap_admin


async def main() -> None:
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password (12–72 characters): ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords do not match")
    try:
        data = BootstrapInput(username=username, email=email, password=password)
    except ValueError:
        raise SystemExit("Invalid input; check email, username and password length") from None
    media = TemporaryDirectory(prefix="lgg-bootstrap-")
    config = create_config(media_root=Path(media.name))
    if config.env.mode == "TEST":
        require_test_config(config)
    try:
        async with config.db_connection.session_local() as session:
            created = await bootstrap_admin(session, data, CryptContext(schemes=["bcrypt"]))
            print("Admin created" if created else "Admin already exists; no changes made")
    except Exception:
        raise SystemExit("Bootstrap failed; check database migrations and account uniqueness") from None
    finally:
        await config.db_connection.engine.dispose()
        media.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
