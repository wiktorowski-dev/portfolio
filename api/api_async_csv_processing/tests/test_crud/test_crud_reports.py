import pytest
import uuid
from datetime import datetime

from app.crud.reports import get_customer_summary
from app.models.transactions import Transaction


@pytest.mark.asyncio
async def test_get_customer_summary_empty(session_factory):
    result = await get_customer_summary(
        customer_id=uuid.uuid4(),
        session_factory=session_factory,
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_customer_summary_with_data(session_factory):
    cid = uuid.uuid4()
    ts1 = datetime(2021, 1, 1, 12, 0)
    ts2 = datetime(2021, 1, 2, 12, 0)
    async with session_factory() as session:
        async with session.begin():
            t1 = Transaction(
                transaction_id=uuid.uuid4(),
                timestamp=ts1,
                amount=100.0,
                currency="PLN",
                customer_id=cid,
                product_id=uuid.uuid4(),
                quantity=1,
            )
            t2 = Transaction(
                transaction_id=uuid.uuid4(),
                timestamp=ts2,
                amount=50.0,
                currency="EUR",
                customer_id=cid,
                product_id=uuid.uuid4(),
                quantity=2,
            )
            session.add_all([t1, t2])

    report = await get_customer_summary(
        customer_id=cid,
        session_factory=session_factory,
    )
    assert report.unique_products == 2
    assert report.total_spent == 315.0
    assert report.last_transaction == ts2
