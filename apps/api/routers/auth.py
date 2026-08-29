"""
ATHENA Authentication & User Management Router
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from packages.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from packages.schemas.auth import Token, UserCreate, UserLogin, UserResponse, UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# In-memory user store with pre-seeded institutional users
MOCK_USERS_DB = {
    "admin": {
        "id": "usr-admin-01",
        "username": "admin",
        "email": "admin@athena-fund.ai",
        "hashed_password": get_password_hash("AthenaAdmin2026!"),
        "full_name": "Chief Investment Officer",
        "role": UserRole.ADMIN,
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "trader": {
        "id": "usr-trader-01",
        "username": "trader",
        "email": "trader@athena-fund.ai",
        "hashed_password": get_password_hash("AthenaTrader2026!"),
        "full_name": "Head Algorithmic Trader",
        "role": UserRole.TRADER,
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "researcher": {
        "id": "usr-researcher-01",
        "username": "researcher",
        "email": "researcher@athena-fund.ai",
        "hashed_password": get_password_hash("AthenaQuant2026!"),
        "full_name": "Senior Quant Researcher",
        "role": UserRole.RESEARCHER,
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        username = payload.get("username")
        if not username or username not in MOCK_USERS_DB:
            raise HTTPException(status_code=401, detail="Invalid user credentials")
        u = MOCK_USERS_DB[username]
        return UserResponse(**u)
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    user = MOCK_USERS_DB.get(credentials.username)
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "role": user["role"].value}
    )
    refresh_token = create_refresh_token(
        data={"sub": user["id"], "username": user["username"], "role": user["role"].value}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,
        user=UserResponse(**user),
    )


@router.post("/refresh")
async def refresh_token(token_data: dict):
    refresh_tok = token_data.get("refresh_token")
    if not refresh_tok:
        raise HTTPException(status_code=400, detail="Missing refresh token")
    payload = decode_token(refresh_tok)
    new_access = create_access_token(
        data={"sub": payload["sub"], "username": payload["username"], "role": payload["role"]}
    )
    return {"access_token": new_access, "token_type": "bearer", "expires_in": 3600}


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    return current_user
