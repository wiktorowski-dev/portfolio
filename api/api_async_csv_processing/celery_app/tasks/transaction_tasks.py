import polars as pl
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import re
import asyncio
import polars.selectors as cs

from app.utils import database
from app.models import transactions as transactions_model
from celery_app.celery_worker import celery_app


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


@celery_app.task(queue="transactions", name="transaction_tasks.process_transactions_file")
def process_transactions_file(csv_content: str) -> dict[str, int]:
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

    # for row in bad_df.rows(named=True):
    #     logging.warning("Invalid transaction skipped: %s", row)
    #
    # records = good_df.to_dicts()
    # asyncio.run(_insert_transactions(records))

    print('Processed')
    return {"inserted": len(good_df), "rejected": len(bad_df)}