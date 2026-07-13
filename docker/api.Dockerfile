FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY apps/api ./apps/api
RUN pip install --no-cache-dir -e .
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000"]
