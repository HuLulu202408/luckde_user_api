
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# 读取 .env 文件，覆盖系统环境变量（仅在本地开发环境使用，生产环境请通过容器 / 云平台配置环境变量）
load_dotenv()
# 下面的配置值仅用于本地开发环境，生产环境请通过环境变量覆盖。
host:str = "192.168.1.36"
port:int = 3308

database_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST", host),
    port=int(os.getenv("MYSQL_PORT", port)),
    database=os.getenv("MYSQL_DATABASE"),
    query={"charset": "utf8mb4"},
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def check_mysql():
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT 1")
        ).scalar_one()
