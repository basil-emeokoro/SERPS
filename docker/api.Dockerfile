FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY apps/api ./apps/api
RUN pip install --no-cache-dir -e .
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY scripts/dev/seed_demo_data.py ./scripts/dev/seed_demo_data.py
COPY scripts/deploy ./scripts/deploy
EXPOSE 8000
CMD ["python", "scripts/deploy/start_api.py"]
