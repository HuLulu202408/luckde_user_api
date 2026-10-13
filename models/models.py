
from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Date, DateTime, String, Text,
    TIMESTAMP, Integer, SmallInteger, text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserBase(Base):
    __tablename__ = "table_userbase"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    gender: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    nickname: Mapped[str | None] = mapped_column(String(100))
    birth: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(100))
    mail: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    avatar: Mapped[str | None] = mapped_column(String(200))
    creattime: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updatetime: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    signature: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )


class Registration(Base):
    __tablename__ = "table_registration"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    deviceid: Mapped[str | None] = mapped_column(String(100))
    regist_type: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    appleid: Mapped[str | None] = mapped_column(String(100))
    googleid: Mapped[str | None] = mapped_column(String(100))
    userid: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account: Mapped[str | None] = mapped_column(String(100))
    password: Mapped[str | None] = mapped_column(String(100))
    channel: Mapped[str | None] = mapped_column(String(100))
    platform: Mapped[str | None] = mapped_column(String(100))
    schema: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[str | None] = mapped_column(String(100))
    version_code: Mapped[str | None] = mapped_column(String(100))
    creattime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updatetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    is_delete: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    is_enable: Mapped[int | None] = mapped_column(
        SmallInteger, server_default=text("1")
    )


class UserWallet(Base):
    __tablename__ = "table_userWallet"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    userid: Mapped[int | None] = mapped_column(BigInteger)
    cash: Mapped[int | None] = mapped_column(
        BigInteger, server_default=text("0")
    )
    score: Mapped[int | None] = mapped_column(
        BigInteger, server_default=text("0")
    )
    creattime: Mapped[datetime | None] = mapped_column(DateTime)
    updatetime: Mapped[datetime | None] = mapped_column(DateTime)
