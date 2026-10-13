
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

load_dotenv()

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
