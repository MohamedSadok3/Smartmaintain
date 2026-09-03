FROM python:3.11-slim

WORKDIR /app
COPY backend/migrations/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/migrations/ .

CMD ["python", "run_migrations.py"]
