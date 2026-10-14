from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models.models import UserBase, Registration, UserWallet
from app.schema import RegisterRequest
from app.security import hash_password
from app.security import verify_password
from app.core.config import settings

# 软删除的历史凭证需要让出 account 唯一键，改写为「此前缀 + 主键」的墓碑值，
# 既释放唯一键，又保留该账号存在过的痕迹。主键唯一保证墓碑值不会重复。
DELETED_ACCOUNT_PREFIX = "#deleted#"


def register_account(db: Session, data: RegisterRequest) -> UserBase:
    with db.begin():
        existing = db.scalar(
            select(Registration)
            .where(
                Registration.account == data.account,
                Registration.regist_type == 0,
            )
            .with_for_update()
        )

        if existing is not None:
            if existing.is_delete == 0:
                # 存在未删除的同名账号（含被禁用的账号），视为名称已占用
                raise ValueError("ACCOUNT_EXISTS")

            # 账号此前被软删除：旧行仍占用 account 唯一键，直接插入必然冲突，
            # 先把旧行改写为墓碑值，再插入全新账号。
            existing.account = f"{DELETED_ACCOUNT_PREFIX}{existing.id}"
            existing.updatetime = datetime.now()
            db.flush()

        user = UserBase(
            nickname=data.nickname,
            mail=data.mail,
            gender=data.gender,
            status=1,
        )
        db.add(user)
        db.flush()

        registration = Registration(
            userid=user.id,
            regist_type=0,
            account=data.account,
            password=hash_password(data.password),
            deviceid=data.deviceid,
            channel=data.channel,
            platform=data.platform,
            schema=data.schema,
            version=data.version,
            version_code=data.version_code,
            is_delete=0,
            is_enable=1,
        )
        db.add(registration)

        now = datetime.now()
        db.add(
            UserWallet(
                userid=user.id,
                cash=0,
                score=0,
                creattime=now,
                updatetime=now,
            )
        )

        db.flush()

    # 事务提交后，user 对象的主键及数据可用于返回
    return user

def authenticate_account(
    db: Session,
    account: str,
    password: str,
) -> UserBase | None:
    result = db.execute(
        select(Registration, UserBase)
        .join(UserBase, Registration.userid == UserBase.id)
        .where(
            Registration.account == account,
            Registration.regist_type == 0,
            Registration.is_delete == 0,
            Registration.is_enable == 1,
            UserBase.status == 1,
        )
    ).first()

    if result is None:
        return None

    registration, user = result

    if not registration.password:
        return None

    if not verify_password(password, registration.password):
        return None

    return user

def login_or_register_social(
    db: Session,
    provider: str,
    identity: dict,
    metadata: dict,
) -> UserBase:
    if provider == "apple":
        field = Registration.appleid
        regist_type = 2
    elif provider == "google":
        field = Registration.googleid
        regist_type = 3
    else:
        raise ValueError("UNSUPPORTED_PROVIDER")

    subject = identity["subject"]

    with db.begin():
        registration = db.scalar(
            select(Registration)
            .where(
                field == subject,
                Registration.regist_type == regist_type,
                Registration.is_delete == 0,
            )
            .with_for_update()
        )

        if registration:
            if registration.is_enable != 1:
                raise ValueError("ACCOUNT_DISABLED")

            user = db.get(UserBase, registration.userid)

            if user is None or user.status != 1:
                raise ValueError("ACCOUNT_DISABLED")

            registration.updatetime = datetime.now()
            return user

        # 首次第三方登录：创建新用户
        user = UserBase(
            status=1,
            nickname=identity.get("name"),
            mail=identity.get("email"),
        )
        db.add(user)
        db.flush()

        registration = Registration(
            userid=user.id,
            regist_type=regist_type,
            appleid=subject if provider == "apple" else None,
            googleid=subject if provider == "google" else None,
            deviceid=metadata.get("deviceid"),
            channel=metadata.get("channel"),
            platform=metadata.get("platform"),
            version=metadata.get("version"),
            version_code=metadata.get("version_code"),
            is_delete=0,
            is_enable=1,
        )
        db.add(registration)

        now = datetime.now()
        db.add(
            UserWallet(
                userid=user.id,
                cash=0,
                score=0,
                creattime=now,
                updatetime=now,
            )
        )

        db.flush()

    return user
