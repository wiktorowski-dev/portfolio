import polars as pl
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, UTC
import os
import re
import asyncio
import polars.selectors as cs

from app.utils import database
from app.models import transactions as transactions_model
from app.models import task as task_model
from celery_app.celery_worker import celery_app
from celery_app.config import settings


UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)

ALLOWED_CURRENCIES = {"PLN", "EUR", "USD"}


async def _insert_transactions(records: list[dict], session):
    async with session() as session:
        async with session.begin():
            objs = [
                transactions_model.Transaction(
                    transaction_id=row["transaction_id"],
                    timestamp=row["timestamp"],
                    amount=row["amount"],
                    currency=row["currency"],
                    customer_id=row["customer_id"],
                    product_id=row["product_id"],
                    quantity=row["quantity"],
                )
                for row in records
            ]
            session.add_all(objs)


async def _insert_task_details(task_id: str, correct_records_count: int, incorrect_records_count: int, session):
    async with session() as session:
        async with session.begin():
            task_obj = task_model.Task(
                task_id=task_id,
                correct_records_count=correct_records_count,
                incorrect_records_count=incorrect_records_count,
            )
            session.add_all([task_obj])


@celery_app.task(bind=True, queue="transactions", name="transaction_tasks.process_transactions_file")
def process_transactions_file(self, csv_content: str) -> dict[str, int]:
    """
    Validate, split and load transactions.
    """

    expected_cols = [
        "transaction_id", "timestamp", "amount", "currency",
        "customer_id", "product_id", "quantity"
    ]
    df_raw = pl.read_csv(
        csv_content.encode("utf8"),
        has_header=True,
        infer_schema_length=0,
        dtypes={col: pl.Utf8 for col in expected_cols}
    )

    missing = set(expected_cols) - set(df_raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = (
        df_raw
        .with_row_index(name='n')
        .with_columns([
            # UUID checks
            pl.col("transaction_id")
                .map_elements(lambda x: bool(UUID_RE.fullmatch(str(x))), return_dtype=pl.Boolean)
                .alias("_v_transaction_id"),

            pl.col("customer_id")
                .map_elements(lambda x: bool(UUID_RE.fullmatch(str(x))), return_dtype=pl.Boolean)
                .alias("_v_customer_id"),

            pl.col("product_id")
                .map_elements(lambda x: bool(UUID_RE.fullmatch(str(x))), return_dtype=pl.Boolean)
                .alias("_v_product_id"),

            # Timestamp must parse
            pl.col("timestamp")
                .str.strptime(pl.Datetime, strict=False)
                .is_not_null()
                .alias("_v_timestamp"),

            # Amount must be a float
            pl.col("amount")
                .cast(pl.Float64, strict=False)
                .is_not_null()
                .alias("_v_amount"),

            # Quantity must be an int
            pl.col("quantity")
                .cast(pl.Int64, strict=False)
                .is_not_null()
                .alias("_v_quantity"),

            # Currency in allowed set
            pl.col("currency")
                .is_in(list(ALLOWED_CURRENCIES))
                .alias("_v_currency"),
        ])
    )

    bad_df = (
        df
        .filter(
            ~pl.any_horizontal(cs.starts_with("_v"))
        )
    )

    good_df = (
        df
        .join(
            bad_df,
            on='n',
            how='anti'
        )
        .select(~cs.starts_with("_v"))
        .drop('n')
        .with_columns([
            pl.col("timestamp").str.strptime(pl.Datetime, strict=False),
            pl.col("amount").cast(pl.Float64),
            pl.col("quantity").cast(pl.Int64)
        ])
    )

    session = database.create_async_db_connection(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        db=settings.postgres_db
    )

    records = good_df.to_dicts()


    loop = asyncio.new_event_loop()

    loop.run_until_complete(_insert_transactions(records, session))
    loop.run_until_complete(_insert_task_details(
        self.request.id,
        len(good_df),
        len(bad_df),
        session
    )
    )


    return {"inserted": len(good_df), "rejected": len(bad_df)}