from google.auth.transport.requests import Request
from google.oauth2 import id_token
from app.core.config import settings
import jwt
from jwt import PyJWKClient


def verify_google_token(raw_token: str) -> dict:

    if not settings.google_login_enabled:
        # 路由层应在入口处就拦截；走到这里说明调用方绕过了开关，属于编码错误。
        raise RuntimeError("GOOGLE_CLIENT_ID 未配置，Google 登录入口应处于关闭状态")

    info = id_token.verify_oauth2_token(
        raw_token,
        Request(),
        settings.GOOGLE_CLIENT_ID,
    )

    subject = info.get("sub")
    if not subject:
        raise ValueError("INVALID_GOOGLE_TOKEN")

    return {
        "subject": subject,
        "email": info.get("email"),
        "email_verified": info.get("email_verified", False),
        "name": info.get("name"),
        "picture": info.get("picture"),
    }

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
apple_jwks = PyJWKClient(APPLE_JWKS_URL)


def verify_apple_token(raw_token: str) -> dict:

    if not settings.apple_login_enabled:
        raise RuntimeError("APPLE_CLIENT_ID 未配置，Apple 登录入口应处于关闭状态")

    signing_key = apple_jwks.get_signing_key_from_jwt(raw_token)
    claims = jwt.decode(
        raw_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.APPLE_CLIENT_ID,
        issuer="https://appleid.apple.com",
        options={"require": ["exp", "iat", "sub"]},
    )

    return {
        "subject": claims["sub"],
        "email": claims.get("email"),
        "email_verified": claims.get("email_verified", False),
    }
