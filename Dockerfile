
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY models ./models
COPY routers ./routers
COPY services ./services

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# 本地开发时使用 --reload，修改代码后自动重载。
# Docker 运行时不使用 --reload，通过镜像和容器部署经过确认的代码版本。
