from fastapi import HTTPException, status


MISSING_TRANSACTION = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing transaction")
MISSING_PRODUCT = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing product")
MISSING_CUSTOMER = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing customer")
INCORRECT_FILE_TYPE = HTTPException(status_code=400, detail="File must be a CSV")
