from fastapi import FastAPI

from app.config import settings
from app.routers import router

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}