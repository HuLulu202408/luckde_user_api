
from datetime import date, datetime

from sqlalchemy import (
    Date, DateTime, Integer, SmallInteger, String, Text,
    TIMESTAMP, Index, text
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.db_session import Base

# 下列类型别名以现网 DDL（MySQL 8）为准：现网整型列带 unsigned，而通用
# BigInteger/SmallInteger 生成的是有符号列。sqlalchemy.dialects.mysql 的类型
# 在非 MySQL 方言下不保证可编译（TINYINT 没有通用 visit_* 实现），因此统一用
# with_variant 指定 sqlite 侧类型：MySQL 生成与现网一致的 DDL，SQLite 侧可建表。
# 注：SQLite 只把 INTEGER PRIMARY KEY 视作 rowid 别名，故主键额外落到 Integer。
BigIntUnsignedPK = mysql.BIGINT(unsigned=True).with_variant(Integer, "sqlite")
BigIntUnsigned = mysql.BIGINT(unsigned=True)
BigIntSignedPK = mysql.BIGINT().with_variant(Integer, "sqlite")
BigIntSigned = mysql.BIGINT()
TinyIntUnsigned = mysql.TINYINT(unsigned=True).with_variant(SmallInteger, "sqlite")
TinyIntSigned = mysql.TINYINT().with_variant(SmallInteger, "sqlite")
IntUnsigned = mysql.INTEGER(unsigned=True)


class UserBase(Base):
    __tablename__ = "table_userbase"

    id: Mapped[int] = mapped_column(
        BigIntUnsignedPK, primary_key=True, autoincrement=True
    )
    gender: Mapped[int] = mapped_column(
        TinyIntUnsigned, nullable=False, server_default=text("0")
    )
    nickname: Mapped[str | None] = mapped_column(String(100))
    birth: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(100))
    mail: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[int] = mapped_column(
        TinyIntSigned, nullable=False, server_default=text("0")
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
        IntUnsigned, nullable=False, server_default=text("0")
    )


class Registration(Base):
    __tablename__ = "table_registration"

    # 与现网约束保持一致（索引名同名，便于新环境一次建对）：
    # account 与 regist_type 联合唯一，使用户名（regist_type=0）与未来的手机号
    # （regist_type=1）不会互相占用；appleid/googleid 各自唯一。
    __table_args__ = (
        Index("uk_registration_account_type", "account", "regist_type", unique=True),
        Index("uk_registration_appleid", "appleid", unique=True),
        Index("uk_registration_googleid", "googleid", unique=True),
    )

    id: Mapped[int] = mapped_column(
        BigIntUnsignedPK, primary_key=True, autoincrement=True
    )
    deviceid: Mapped[str | None] = mapped_column(String(100))
    regist_type: Mapped[int] = mapped_column(
        TinyIntUnsigned, nullable=False, server_default=text("0")
    )
    appleid: Mapped[str | None] = mapped_column(String(100))
    googleid: Mapped[str | None] = mapped_column(String(100))
    userid: Mapped[int] = mapped_column(BigIntUnsigned, nullable=False)
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
        TinyIntSigned, nullable=False, server_default=text("0")
    )
    is_enable: Mapped[int | None] = mapped_column(
        TinyIntSigned, server_default=text("1")
    )


class UserWallet(Base):
    __tablename__ = "table_userWallet"

    id: Mapped[int] = mapped_column(
        BigIntSignedPK, primary_key=True, autoincrement=True
    )
    userid: Mapped[int | None] = mapped_column(BigIntSigned)
    cash: Mapped[int | None] = mapped_column(
        BigIntSigned, server_default=text("0")
    )
    score: Mapped[int | None] = mapped_column(
        BigIntSigned, server_default=text("0")
    )
    creattime: Mapped[datetime | None] = mapped_column(DateTime)
    updatetime: Mapped[datetime | None] = mapped_column(DateTime)
