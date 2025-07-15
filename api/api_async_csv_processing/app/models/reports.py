from pydantic import BaseModel, model_validator
from datetime import datetime


def _round_currency(value: float) -> float:
    return round(value, 2)


class CustomerReport(BaseModel):
    total_spent: float
    unique_products: int
    last_transaction: datetime

    @model_validator(mode="before")
    def round_values(cls, values):
        if 'total_spent' in values:
            values['total_spent'] = _round_currency(values['total_spent'])
        return values


class ProductReport(BaseModel):
    total_quantity: int
    total_revenue_pln: float
    unique_customers: int

    @model_validator(mode="before")
    def round_values(cls, values):
        if 'total_revenue_pln' in values:
            values['total_revenue_pln'] = _round_currency(values['total_revenue_pln'])
        return values


