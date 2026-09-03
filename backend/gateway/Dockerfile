FROM python:3.11-slim
WORKDIR /app
COPY backend/gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/gateway/ .
COPY backend/shared ./shared
CMD ["python", "app.py"]
