from pydantic import BaseModel


class CurrencyRates(BaseModel):
    """Currency rates to PLN"""

    USD: float = 4.0
    EUR: float = 4.3
    PLN: float = 1.0
