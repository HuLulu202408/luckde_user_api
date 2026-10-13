from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import UserBase, Registration, UserWallet
from app.schemas import RegisterRequest
from app.security import hash_password
from app.security import verify_password
from app.config import settings

def register_account(db: Session, data: RegisterRequest) -> UserBase:
    with db.begin():
        exists = db.scalar(
            select(Registration.id).where(
                Registration.account == data.account,
                Registration.regist_type == 0,
                Registration.is_delete == 0,
            )
        )
        if exists:
            raise ValueError("ACCOUNT_EXISTS")

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