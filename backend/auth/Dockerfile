FROM python:3.11-slim
WORKDIR /app
COPY backend/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/auth/ .
COPY backend/shared ./shared
CMD ["python", "app.py"]
