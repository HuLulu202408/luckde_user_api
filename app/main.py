import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.db_session import get_db
from app import security
from routers.router import router

logger = logging.getLogger(__name__)
app = FastAPI(title=settings.APP_NAME)

app.include_router(router)

# 文档相关路径禁用缓存：Swagger UI 只在页面加载时拉一次 openapi.json，
# 浏览器或边缘缓存里的旧 spec 会让人误以为新代码没生效——发版后仍看到
# 旧接口/旧参数框就是这么来的。
DOCS_PATHS = {"/openapi.json", "/docs", "/redoc"}


@app.middleware("http")
async def disable_docs_caching(request: Request, call_next):
    """给文档端点加 no-store，保证每次刷新都拿到最新接口定义。"""
    response = await call_next(request)
    if request.url.path in DOCS_PATHS:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health():
    """存活检查：只表示进程在运行，不探测依赖，供容器编排做 liveness。"""
    return {"status": "ok"}

@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    """就绪检查：探测 MySQL 与 Redis，任一不可用返回 503 并指出是哪个组件。

    部署排障用（例如 Redis 容器用 --requirepass 启动但未配置 REDIS_PASSWORD 时，
    这里会直接给出 redis 组件失败），生产环境建议仅在内部网络暴露。
    """
    failed: dict[str, str] = {}

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 诊断端点：任何异常都应被报告而不是 500
        logger.warning("就绪检查失败（MySQL）: %s: %s", type(exc).__name__, exc)
        failed["mysql"] = type(exc).__name__

    try:
        # 通过模块访问，保证与 routers 使用的是同一个客户端对象（也便于测试替换）
        security.redis_client.ping()
    except Exception as exc:  # noqa: BLE001 同上
        logger.warning("就绪检查失败（Redis）: %s: %s", type(exc).__name__, exc)
        failed["redis"] = type(exc).__name__

    if failed:
        raise HTTPException(503, detail={"status": "unavailable", "failed": failed})

    return {"status": "ok", "mysql": "ok", "redis": "ok"}
