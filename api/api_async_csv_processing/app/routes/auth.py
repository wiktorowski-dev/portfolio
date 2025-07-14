from fastapi import Depends, HTTPException, APIRouter, Query, UploadFile, File


router = APIRouter()


@router.get("/sign_in")
def sign_in(transaction_id: str):
    ...


@router.get("/sign_up")
def sign_up():
    ...


@router.get("/")
def list_transactions(customer_id: str = None, product_id: str = None,  page: int = Query(default=1, ge=1)):
    ...

