from fastapi import FastAPI

from app.core.config import settings
from routers.router import router

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}