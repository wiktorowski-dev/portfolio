from fastapi import Depends, HTTPException, APIRouter


router = APIRouter()


@router.get("customer-summary/{customer_id}")
def get_customer_summary(customer_id: str):
    ...


@router.get("product-summary/{product_id}")
def get_customer_summary(product_id: str):
    ...


