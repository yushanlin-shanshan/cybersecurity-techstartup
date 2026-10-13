FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DATA_DIR=/data
EXPOSE 8000
CMD ["sh", "-c", "python -m backend.cli demo && exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
