from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.crud import data as data_crud
from app.dependencies.auth_dependencies import get_current_user

router = APIRouter()


@router.get("/internal_data")
async def get_internal_data(_ = Depends(get_current_user)):
    return JSONResponse(await data_crud.get_internal_data())

