from fastapi import HTTPException, status


MISSING_PRODUCT = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing product")
MISSING_CUSTOMER = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing customer")
