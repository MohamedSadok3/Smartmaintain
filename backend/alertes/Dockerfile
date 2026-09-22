FROM python:3.11-slim
WORKDIR /app
COPY backend/alertes/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/alertes/ .
COPY backend/shared ./shared
CMD ["python", "app.py"]
