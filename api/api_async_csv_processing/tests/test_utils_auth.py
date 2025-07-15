import pytest
from jose import JWTError, jwt

from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    SECRET_KEY,
    ALGORITHM,
)


def test_hash_and_verify_password():
    plain = "Str0ng#Pass!"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_token():
    payload = {"sub": "user@example.com"}
    token = create_access_token(payload)

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user@example.com"

    assert decode_access_token(token) == "user@example.com"


def test_decode_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_access_token("not.a.real.token")
