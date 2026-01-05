from typing import TypeVar

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update

from .base import Base, sessionmaker

SchemaT = TypeVar("SchemaT", bound=BaseModel)
ModelT = TypeVar("ModelT", bound=Base)


async def create[SchemaT: BaseModel, ModelT: Base](
        schema: SchemaT, *, model_class: type[ModelT]
) -> None:
    async with sessionmaker() as session:
        stmt = insert(model_class).values(**schema.model_dump())
        await session.execute(stmt)
        await session.commit()


async def read[SchemaT: BaseModel, ModelT: Base](
        id: UUID, *, model_class: type[ModelT], schema_class: type[SchemaT]  # noqa: A002
) -> SchemaT | None:
    async with sessionmaker() as session:
        stmt = select(model_class).where(model_class.id == id)
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
    return schema_class.model_validate(model) if model is not None else None


async def refresh[SchemaT: BaseModel, ModelT: Base](
        id: UUID, *, model_class: type[ModelT], schema_class: type[SchemaT], **kwargs  # noqa: A002
) -> SchemaT:
    async with sessionmaker() as session:
        stmt = (
            update(model_class)
            .where(model_class.id == id)
            .values(**kwargs)
            .returning(model_class)
        )
        result = await session.execute(stmt)
        await session.commit()
        model = result.scalar_one_or_none()
    return schema_class.model_validate(model) if model is not None else None


async def remove[ModelT: Base](id: UUID, *, model_class: type[ModelT]) -> None:  # noqa: A002
    async with sessionmaker() as session:
        stmt = delete(model_class).where(model_class.id == id)
        await session.execute(stmt)
        await session.commit()
