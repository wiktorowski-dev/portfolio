from fastapi import HTTPException, status


INCORRECT_USERNAME_OR_PASSWORD = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
USERNAME_ALREADY_EXISTS = HTTPException(status_code=400, detail="Username already exists")
USER_NOT_CONFIRMED = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not confirmed")
PASSWORD_TOO_SHORT = HTTPException(status_code=422, detail="Password must be at least 8 characters long")
PASSWORD_WITHOUT_UPPERCASE = HTTPException(status_code=422, detail="Password must contain at least one uppercase letter")
PASSWORD_WITHOUT_LOWERCASE = HTTPException(status_code=422, detail="Password must contain at least one lowercase letter")
PASSWORD_WITHOUT_NUMBER = HTTPException(status_code=422, detail="Password must contain at least one number")
INVALID_TOKEN_OR_PASSWORD = HTTPException(status_code=401, detail="Invalid access token or current password")
INVALID_PARAMETERS = HTTPException(status_code=400, detail="Invalid parameters")
USER_CODE_400 = HTTPException(status_code=400, detail="Something went wrong")
