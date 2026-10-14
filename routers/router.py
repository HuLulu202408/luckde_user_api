
import json
import logging

import redis
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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

# 声明成标准的安全方案后，Swagger UI 会出现右上角 Authorize 按钮：
# 填一次 token 即对全页生效，不必再往参数框里手写 `Bearer `。
# auto_error=False：缺少凭证时不抛 FastAPI 默认的 403，交给我们自己返回
# 「没带头 / 格式不对 / token 为空」三种可区分的 401。
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="登录接口返回的 token（填原始 token 即可，无需自己加 Bearer 前缀）",
)


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


def describe_authorization_header(value: str) -> str:
    """只描述 Authorization 头的形状，不回显内容（避免把 token 写进日志）。

    典型问题：复制粘贴带出的不换行空格、中文输入法打出的全角空格、
    漏掉 `Bearer ` 前缀。用字符码点表述，一眼就能看出是哪种。
    """
    stripped = value.strip()
    parts = [f"长度={len(value)}"]

    if stripped[:6].lower() == "bearer":
        parts.append("以 Bearer 开头")
        if len(stripped) > 6:
            parts.append(
                f"第 7 位字符码点 U+{ord(stripped[6]):04X}（应为空格 U+0020）"
            )
    else:
        parts.append("未以 Bearer 开头")

    return "，".join(parts)


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
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    # 这里仍直接读原始头：HTTPBearer 在 auto_error=False 时无法区分
    # 「没带这个头」与「scheme 不是 Bearer」，而这两种情况要给不同提示。
    authorization = request.headers.get("authorization", "")

    # 单独区分「没带这个头」与「带了但格式不对」：两者都回同一句话会让
    # Swagger / 网关丢头这类问题无从下手（历史上正是这个原因排查了很久）。
    if not authorization.strip():
        # 记录实际收到的头名（不含值）：如果列表里没有 authorization，
        # 就说明请求根本没带、或被反向代理/隧道吃掉了。
        logger.warning(
            "缺少 Authorization 头：path=%s client=%s 共收到 %d 个头 %s",
            request.url.path,
            request.client.host if request.client else "unknown",
            len(request.headers),
            sorted(request.headers.keys()),
        )
        raise HTTPException(401, "Missing Authorization header")

    # 容忍首尾空白；scheme 按 RFC 7235 做大小写不敏感比较（bearer 亦可）。
    scheme, _, raw_token = authorization.strip().partition(" ")
    token = raw_token.strip()

    if scheme.lower() != "bearer":
        logger.warning(
            "Authorization 头无法识别为 Bearer 方案（%s）",
            describe_authorization_header(authorization),
        )
        raise HTTPException(
            401, 'Authorization header must look like "Bearer <token>"'
        )

    if not token:
        raise HTTPException(401, "Empty bearer token")

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
