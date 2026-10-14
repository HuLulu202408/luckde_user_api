
import json
import logging

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

logger = logging.getLogger(__name__)


def auth_service_unavailable(exc: Exception) -> HTTPException:
    """Redis 故障统一映射为 503，并把真实原因写进日志。

    部署时最常见的是 NOAUTH（容器用 --requirepass 启动但未配置 REDIS_PASSWORD），
    只回 503 会让排查失去线索，因此这里把异常类型与信息打到应用日志。
    """
    logger.warning("认证服务不可用（Redis）: %s: %s", type(exc).__name__, exc)
    return HTTPException(503, "Authentication service unavailable")


def require_provider_enabled(provider: str, client_id_env: str, enabled: bool) -> None:
    """第三方登录未配置时，明确返回「已关闭」而不是让请求走进校验逻辑。"""
    if not enabled:
        raise HTTPException(
            503, f"{provider} login is disabled ({client_id_env} is not configured)"
        )


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
    except redis.RedisError as exc:
        raise auth_service_unavailable(exc)


@router.post("/apple")
def apple_login(
    data: SocialLoginRequest,
    db: Session = Depends(get_db),
):
    require_provider_enabled("Apple", "APPLE_CLIENT_ID", settings.apple_login_enabled)
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
    except redis.RedisError as exc:
        raise auth_service_unavailable(exc)
    except SQLAlchemyError:
        raise HTTPException(503, "Database unavailable")


@router.post("/google")
def google_login(
    data: SocialLoginRequest,
    db: Session = Depends(get_db),
):
    require_provider_enabled("Google", "GOOGLE_CLIENT_ID", settings.google_login_enabled)
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
    except redis.RedisError as exc:
        raise auth_service_unavailable(exc)
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
    except redis.RedisError as exc:
        raise auth_service_unavailable(exc)

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
    except redis.RedisError as exc:
        raise auth_service_unavailable(exc)
