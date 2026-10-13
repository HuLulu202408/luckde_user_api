from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class UserBase(Base):

    __tablename__ = "table_userbase"
    
    """
    用户基础信息模型
    """
    id: Mapped[int] = mapped_column(
        BigInteger, 
        primary_key=True,
        autoincrement=True
    )
    
    username: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    signature: Mapped[str] = mapped_column(
        String(255), 
        nullable=True
    )
    level: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0
    )
    mail: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    gender: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0
    )
    birth: Mapped[str] = mapped_column(
        String(255), 
        nullable=True
    )
    phone: Mapped[str] = mapped_column(
        String(255), 
        nullable=True
    )
    status: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0
    )
    avatar: Mapped[str] = mapped_column(
        String(255), 
        nullable=True
    )
    creattime: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updatetime: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def __init__(self, id: int, username: str, signature: str, level: int, mail: str, gender: int, birth: str,
                 phone: str, status: int, avatar: str, creattime: datetime, updatetime: datetime):
        self.id = id
        self.username = username
        self.signature = signature
        self.level = level
        self.mail = mail
        self.gender = gender
        self.birth = birth
        self.phone = phone
        self.status = status
        self.avatar = avatar
        self.creattime = creattime
        self.updatetime = updatetime  

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "signature": self.signature,
            "level": self.level,
            "mail": self.mail,
            "gender": self.gender,
            "birth": self.birth,
            "phone": self.phone,
            "status": self.status,
            "avatar": self.avatar,
            "creattime": self.creattime,
            "updatetime": self.updatetime
        }
    
    
