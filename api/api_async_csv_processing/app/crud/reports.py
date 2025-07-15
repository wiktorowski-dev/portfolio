from sqlalchemy import select, func, case
import uuid

from app.models.transactions import Transaction
from app.models import reports as reports_model
from app.models.currency import CurrencyRates


async def get_customer_summary(*, customer_id: uuid.uuid4, session_factory, start_date: str = None, end_date: str = None):
    currency_rates = CurrencyRates()

    stmt = (
        select(
            func.sum(
                case(
                    (Transaction.currency == 'PLN', Transaction.amount * currency_rates.PLN),
                    (Transaction.currency == 'EUR', Transaction.amount * currency_rates.EUR),
                    (Transaction.currency == 'USD', Transaction.amount * currency_rates.USD),
                    else_=0.0
                )
            ).label("total_spent"),
            func.count(func.distinct(Transaction.product_id)).label("unique_products"),
            func.max(Transaction.timestamp).label("last_transaction")
        )
        .where(Transaction.customer_id == customer_id)
    )

    if start_date:
        stmt = stmt.where(Transaction.timestamp >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.timestamp <= end_date)

    async with session_factory() as session:
        result = await session.execute(stmt)
        row = result.mappings().one_or_none()
        result = dict(row)

    if any([v is None for v in result.values()]):
        return None

    return reports_model.CustomerReport(**result)


async def get_product_summary(*, product_id: str, session_factory, start_date: str = None, end_date: str = None):
    currency_rates = CurrencyRates()

    stmt = (
        select(
            func.sum(Transaction.quantity).label("total_quantity"),
            func.sum(
                case(
                    (Transaction.currency == 'PLN', Transaction.amount * currency_rates.PLN),
                    (Transaction.currency == 'EUR', Transaction.amount * currency_rates.EUR),
                    (Transaction.currency == 'USD', Transaction.amount * currency_rates.USD),
                    else_=0.0
                )
            ).label("total_revenue_pln"),
            func.count(func.distinct(Transaction.customer_id)).label("unique_customers")
        )
        .where(Transaction.product_id == product_id)
    )

    if start_date:
        stmt = stmt.where(Transaction.timestamp >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.timestamp <= end_date)

    async with session_factory() as session:
        row = (await session.execute(stmt)).mappings().one_or_none()
        result = dict(row)

    if any([v is None for v in result.values()]):
        return None

    return reports_model.ProductReport(**result)
