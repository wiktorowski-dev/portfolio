from fastapi import Depends, HTTPException, APIRouter


router = APIRouter()


@router.get("/sign_in")
def sign_in():
    ...


@router.get("/sign_up")
def sign_up():
    ...

