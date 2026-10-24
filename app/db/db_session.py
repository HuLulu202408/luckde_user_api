
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

# 下面的配置值仅用于本地开发环境，生产环境请通过环境变量覆盖。
database_url = URL.create(
    drivername="mysql+pymysql",
    username=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    host=settings.MYSQL_HOST,
    port=settings.MYSQL_PORT,
    database=settings.MYSQL_DATABASE,
    query={"charset": "utf8mb4"},
)
#engine：管理数据库连接和连接池，通常整个应用共享一个 Engine。
# pool_size=5：默认连接池保留的连接数量。
# max_overflow=10：高峰时允许临时增加的连接数。
# pool_pre_ping=True：取用连接时检查连接是否仍然有效。
engine = create_engine(
    database_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
#SessionLocal：用于创建 Session 的工厂，而不是一个已经打开的 Session。
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass

#get_db()：每个请求获取自己的 Session，并在请求结束后关闭它。
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
