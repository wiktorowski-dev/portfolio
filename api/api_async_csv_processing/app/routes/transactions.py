from fastapi import Depends, HTTPException, APIRouter, Query


router = APIRouter()


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str):
    ...


@router.get("/")
def list_transactions(customer_id: str = None, product_id: str = None,  page: int = Query(default=1, ge=1)):
    ...




