# Stage: Build và install dependencies bằng Poetry
FROM python:3.12-slim AS chatbot-service

# Biến môi trường & Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2

# Cài Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Tạo thư mục làm việc
WORKDIR /app

# Copy pyproject và poetry.lock
COPY pyproject.toml poetry.lock ./

# Cài đặt dependencies (không tạo virtualenv)
RUN poetry config virtualenvs.create false \
 && poetry install --no-root --no-interaction --no-ansi

# Copy source code vào container
COPY app/ ./app

# Expose cổng FastAPI (ví dụ: 1210)
EXPOSE 1210

# Chạy FastAPI (entrypoint tại app/main.py)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "1210"]
