
import json

import redis
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.db_session import get_db

from app.schema import (
    RegisterRequest,
    LoginRequest,
    SocialLoginRequest,
)
from services.service import (
    register_account,
    authenticate_account,
    login_or_register_social,
)
from app.security import (
    create_token,
    save_token,
    get_token_user,
    delete_token,
    redis_client,
)
from models import UserBase
from app.security import user_to_json
from app.core.config import settings
from app.security import verify_password
from services.providers import verify_google_token, verify_apple_token

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


def issue_token(user: UserBase) -> dict:
    token = create_token()
    save_token(token, user)

    return {
        "token": token,
        "token_type": "Bearer",
        "expires_in": settings.TOKEN_TTL_SECONDS,
        "user": json.loads(user_to_json(user)),
    }


@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        user = register_account(db, data)
        return {
            "code": 0,
            "message": "Registered successfully",
            "data": {"user_id": user.id},
        }
    except ValueError as exc:
        if str(exc) == "ACCOUNT_EXISTS":
            raise HTTPException(409, "Account already exists")
        raise
    except IntegrityError:
        raise HTTPException(409, "Account already exists")
    except SQLAlchemyError:
        raise HTTPException(503, "Database unavailable")


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_account(db, data.account, data.password)

        if user is None:
            raise HTTPException(401, "Invalid account or password")

        return {
            "code": 0,
            "message": "Login successful",
            "data": issue_token(user),
        }
    except redis.RedisError:
        raise HTTPException(503, "Authentication service unavailable")


@router.post("/apple")
def apple_login(
    data: SocialLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        identity = verify_apple_token(data.id_token)
        user = login_or_register_social(
            db,
            "apple",
            identity,
            data.model_dump(exclude={"id_token"}),
        )
        return {"code": 0, "message": "Login successful", "data": issue_token(user)}
    except ValueError:
        raise HTTPException(401, "Invalid Apple identity token")
    except IntegrityError:
        raise HTTPException(409, "Account registration conflict")
    except redis.RedisError:
        raise HTTPException(503, "Authentication service unavailable")
    except SQLAlchemyError:
        raise HTTPException(503, "Database unavailable")


@router.post("/google")
def google_login(
    data: SocialLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        identity = verify_google_token(data.id_token)
        user = login_or_register_social(
            db,
            "google",
            identity,
            data.model_dump(exclude={"id_token"}),
        )
        return {"code": 0, "message": "Login successful", "data": issue_token(user)}
    except ValueError:
        raise HTTPException(401, "Invalid Google identity token")
    except IntegrityError:
        raise HTTPException(409, "Account registration conflict")
    except redis.RedisError:
        raise HTTPException(503, "Authentication service unavailable")
    except SQLAlchemyError:
        raise HTTPException(503, "Database unavailable")


def require_token(
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")

    token = authorization[7:].strip()
    if not token:
        raise HTTPException(401, "Invalid token")

    try:
        user = get_token_user(token)
    except redis.RedisError:
        raise HTTPException(503, "Authentication service unavailable")

    if user is None:
        raise HTTPException(401, "Token expired or invalid")

    return {"token": token, "user": user}


@router.get("/me")
def me(auth=Depends(require_token)):
    return {"code": 0, "data": auth["user"]}


@router.post("/logout")
def logout(auth=Depends(require_token)):
    try:
        delete_token(auth["token"])
        return {"code": 0, "message": "Logged out"}
    except redis.RedisError:
        raise HTTPException(503, "Authentication service unavailable")
