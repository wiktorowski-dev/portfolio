from sqlalchemy import select, func

from app.models.transactions import Transaction


async def get_customer_summary(customer_id: str):
    total_spent_query = (
        select(
            func.sum(
                func.case(
                    (Transaction.currency == 'PLN', Transaction.amount),
                    (Transaction.currency == 'EUR', Transaction.amount * 4.3),
                    (Transaction.currency == 'USD', Transaction.amount * 4.0),
                    else_=0.0
                )
            ).label("total_spent"),
            func.count(func.distinct(Transaction.product_id)).label("unique_products"),
            func.max(Transaction.timestamp).label("last_transaction")
        )
        .where(Transaction.customer_id == customer_id)
    )
    print('ok')
    return {
        "spend_amount_pln": 0,
        "number_of_items_bought": 0,
        "last_transaction_data": ""
    }


async def get_product_summary(product_id: str, start_date: str, end_date: str):
    return {
        "total_sold_amount": 0,
        "total_revenue_generated": 0,
        "number_of_unique_clients": ""
    }


