"""
ATHENA Security, Cryptography, and RBAC Engine
Uses standard library PBKDF2-HMAC-SHA256 for secure password hashing and python-jose for JWTs.
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from jose import JWTError, jwt

from packages.common.config import settings
from packages.schemas.auth import TokenPayload, UserRole


def get_password_hash(password: str) -> str:
    """Generates a secure PBKDF2-HMAC-SHA256 hash with random salt."""
    salt = os.urandom(16)
    pw_bytes = password.encode("utf-8")
    hash_bytes = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt, 100000)
    return f"{salt.hex()}:{hash_bytes.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against stored PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split(":")
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        stored_hash = bytes.fromhex(parts[1])
        pw_bytes = plain_password.encode("utf-8")
        computed_hash = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt, 100000)
        return hmac.compare_digest(stored_hash, computed_hash)
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a signed JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token signature and expiry."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {str(e)}")


def check_role_permission(user_role: UserRole, required_roles: List[UserRole]) -> bool:
    """RBAC validation: ADMIN has access to all; TRADER has trader/viewer; etc."""
    if user_role == UserRole.ADMIN:
        return True
    return user_role in required_roles
