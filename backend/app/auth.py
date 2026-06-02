import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

security = HTTPBearer()

# Returns a bcrypt hash of the given password.
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Checks a plaintext password against a bcrypt hash.
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Creates a signed JWT with an expiration claim from the given payload.
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Decodes and validates a JWT. Raises 401 on expiry or invalid token.
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Extracts user info from the Authorization header JWT.
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    payload = decode_token(credentials.credentials)
    return {
        "id": payload.get("id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "name": payload.get("name"),
    }

# Extracts user info from a query-param JWT (used by SSE endpoint).
async def get_current_user_query(token: str = Query(...)) -> dict:
    payload = decode_token(token)
    return {
        "id": payload.get("id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "name": payload.get("name"),
    }

# Dependency that rejects non-admin users with 403.
def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Dependency that rejects users without reviewer or admin role.
def require_reviewer(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("reviewer", "admin"):
        raise HTTPException(status_code=403, detail="Reviewer or admin access required")
    return user
