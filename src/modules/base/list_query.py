"""Shared list contracts and one-statement PostgreSQL pagination."""
from enum import StrEnum
from typing import Any, Callable, TypeVar
from sqlalchemy.sql.elements import ColumnElement

from sqlalchemy import Select, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased


class ListView(StrEnum):
    ALL = "all"
    ACTIVE = "active"
    ARCHIVE = "archive"


def view_scope(active: ColumnElement[bool], view: ListView) -> ColumnElement[bool]:
    return active if view == ListView.ACTIVE else ~active if view == ListView.ARCHIVE else true()


Model = TypeVar("Model")


async def snapshot_page(
    session: AsyncSession, model: type[Model], stmt: Select,
    ordering: tuple[Callable[[Any], Any], ...], limit: int, offset: int,
    options: tuple[Callable[[Any], Any], ...] = (),
) -> tuple[list[Model], int]:
    """Count and rows share a statement snapshot, including an empty/out-of-range page."""
    filtered = stmt.cte("filtered")
    entity = aliased(model, filtered)
    total = select(func.count().label("total")).select_from(filtered).subquery()
    page = select(entity).order_by(*(order(entity) for order in ordering)).limit(limit).offset(offset).subquery()
    item = aliased(model, page)
    query = select(item, total.c.total).select_from(total.outerjoin(page, true()))
    query = query.order_by(*(order(item) for order in ordering))
    if options:
        query = query.options(*(option(item) for option in options))
    rows = (await session.execute(query)).all()
    return [row[0] for row in rows if row[0] is not None], rows[0][1]
