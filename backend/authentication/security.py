from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "logvista-dev-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

USERS_DB = {
    "admin": {
        "username": "admin",
        "password_hash": pwd_context.hash("admin123"),
        "role": "Admin",
    },
    "dev": {
        "username": "dev",
        "password_hash": pwd_context.hash("dev123"),
        "role": "Developer",
    },
    "viewer": {
        "username": "viewer",
        "password_hash": pwd_context.hash("viewer123"),
        "role": "Viewer",
    },
}

INGESTION_API_KEYS = {"demo-ingest-key": "sample-client"}


def authenticate_user(username: str, password: str) -> dict | None:
    user = USERS_DB.get(username)
    if not user or not pwd_context.verify(password, user["password_hash"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = USERS_DB.get(username)
    if user is None:
        raise credentials_exception
    return user


def require_role(*allowed_roles: str):
    def _role_guard(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _role_guard


def verify_ingestion_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if not x_api_key or x_api_key not in INGESTION_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid ingestion API key")
    return INGESTION_API_KEYS[x_api_key]
