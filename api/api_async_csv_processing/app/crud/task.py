from sqlalchemy import select, func
from app.models.task import Task


async def get_task_details(task_id: str, session_factory=None) -> Task | None:
    stmt = select(Task).where(Task.task_id == task_id)

    async with session_factory() as session:
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

    if not row:
        return None

    return row


async def list_tasks(session_factory=None, page: int = 1, limit: int = 50) -> list[Task]:
    stmt = select(Task)

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    async with session_factory() as session:
        result = await session.execute(stmt)
        rows = result.scalars().all()

    return rows
