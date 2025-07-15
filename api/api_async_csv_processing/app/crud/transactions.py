from sqlalchemy import select, func
from app.models.transactions import Transaction


async def get_transaction_details(transaction_id: str, session_factory=None) -> Transaction | None:
    stmt = select(Transaction).where(Transaction.transaction_id == transaction_id)

    async with session_factory() as session:
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

    if not row:
        return None

    return row


async def list_transactions(session_factory=None, customer_id=None, product_id=None, page=1, limit=10):
    stmt = select(Transaction)

    if customer_id:
        stmt = stmt.where(Transaction.customer_id == customer_id)
    if product_id:
        stmt = stmt.where(Transaction.product_id == product_id)

    total_stmt = select(func.count()).select_from(stmt.subquery())

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    async with session_factory() as session:
        total_result = await session.execute(total_stmt)
        total = total_result.scalar_one()

        result = await session.execute(stmt)
        transactions = result.scalars().all()

    return total, transactions
