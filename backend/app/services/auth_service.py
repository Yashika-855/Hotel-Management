"""
Authentication service — business logic for login, registration, and token refresh.
Thin wrapper delegating to the database and security utilities.
"""
from datetime import datetime, timezone
from app.database import get_user_collection
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
)
import logging

logger = logging.getLogger("LuxeStayAPI")


async def authenticate_user(email: str, password: str) -> dict:
    """
    Validate email + password and return a Token dict.
    Raises UnauthorizedException on failure.
    """
    users_col = get_user_collection()
    user = await users_col.find_one({"email": email})

    if not user or not verify_password(password, user["hashed_password"]):
        raise UnauthorizedException("Incorrect email or password")

    user_data = {"email": user["email"], "role": user["role"], "name": user["name"]}
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data=user_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user["role"],
        "name": user["name"],
    }


async def register_user(email: str, password: str, name: str, role: str = "user") -> dict:
    """
    Create a new user. Default role is 'user', but 'staff' can be passed.
    Admin role can only be assigned by an existing admin via direct DB update.
    Raises BadRequestException if email already exists.
    """
    users_col = get_user_collection()

    existing = await users_col.find_one({"email": email})
    if existing:
        raise BadRequestException("Email already registered")

    # Ensure only user or staff roles can be registered here
    if role not in ["user", "staff"]:
        role = "user"

    user_dict = {
        "email": email,
        "hashed_password": get_password_hash(password),
        "role": role,
        "name": name,
        "created_at": datetime.now(timezone.utc),
    }

    result = await users_col.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    logger.info(f"New staff user registered: {email}")
    return user_dict


async def refresh_tokens(refresh_token_str: str) -> dict:
    """
    Validate a refresh token and issue a new access + refresh token pair.
    Raises UnauthorizedException on invalid/expired refresh token.
    """
    payload = decode_refresh_token(refresh_token_str)
    if not payload:
        raise UnauthorizedException("Invalid or expired refresh token")

    email = payload.get("email")
    if not email:
        raise UnauthorizedException("Invalid refresh token payload")

    users_col = get_user_collection()
    user = await users_col.find_one({"email": email})
    if not user:
        raise UnauthorizedException("User not found")

    user_data = {"email": user["email"], "role": user["role"], "name": user["name"]}
    access_token = create_access_token(data=user_data)
    new_refresh_token = create_refresh_token(data=user_data)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "role": user["role"],
        "name": user["name"],
    }
