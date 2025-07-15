from fastapi import Depends, HTTPException, APIRouter
from typing import Optional
from datetime import datetime
from pydantic import UUID4

from app.crud import reports
from app.dependencies import db_session as db_session_dependency
from app import exceptions
from app.models import reports as reports_models
from app.dependencies.auth import get_current_user


router = APIRouter()


@router.get("/customer-summary/{customer_id}")
async def get_customer_summary(
        customer_id: UUID4,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db_session = Depends(db_session_dependency.get_db_session),
        _ = Depends(get_current_user)
) -> reports_models.CustomerReport:
    report = await reports.get_customer_summary(
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        session_factory=db_session
    )

    if not report:
        raise exceptions.MISSING_CUSTOMER

    return report


@router.get("/product-summary/{product_id}")
async def get_product_summary(
        product_id: UUID4,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db_session = Depends(db_session_dependency.get_db_session),
        _ = Depends(get_current_user)
) -> reports_models.ProductReport:
    report = await reports.get_product_summary(
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        session_factory=db_session
    )

    if not report:
        raise exceptions.MISSING_PRODUCT

    return report



