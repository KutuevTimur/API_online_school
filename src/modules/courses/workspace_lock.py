"""Workspace creation mutex shared by public and F01 identity consumers."""
import hashlib
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def lock_workspace_pair(session: AsyncSession, teacher_id: int, student_id: int) -> None:
    key = int.from_bytes(hashlib.sha256(f'{teacher_id}:{student_id}'.encode()).digest()[:4],
                         'big', signed=True)
    await session.execute(text('SELECT pg_advisory_xact_lock(80421, :key)'), {'key': key})
