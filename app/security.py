import json
import secrets
import redis
from pwdlib import PasswordHash
import app.core.config

password_hash = PasswordHash.recommended()

redis_client = redis.Redis(
    host=app.core.config.settings.REDIS_HOST,
    port=app.core.config.settings.REDIS_PORT,
    db=app.core.config.settings.REDIS_DB,
    password=app.core.config.settings.REDIS_PASSWORD or None,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_hash.verify(password, hashed)
    except Exception:
        return False


def create_token() -> str:
    return secrets.token_urlsafe(32)


def user_to_json(user) -> str:
    data = {
        "id": user.id,
        "gender": user.gender,
        "nickname": user.nickname,
        "birth": user.birth.isoformat() if user.birth else None,
        "phone": user.phone,
        "mail": user.mail,
        "status": user.status,
        "avatar": user.avatar,
        "signature": user.signature,
        "level": user.level,
    }
    return json.dumps(data, ensure_ascii=False)


def save_token(token: str, user) -> None:
    key = f"auth:token:{token}"
    redis_client.set(
        key,
        user_to_json(user),
        ex=app.core.config.settings.TOKEN_TTL_SECONDS,
    )


def get_token_user(token: str):
    raw = redis_client.get(f"auth:token:{token}")
    return json.loads(raw) if raw else None


def delete_token(token: str) -> None:
    redis_client.delete(f"auth:token:{token}")