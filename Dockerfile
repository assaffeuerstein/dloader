FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

RUN useradd -m appuser \
    && mkdir -p /download \
    && chown -R appuser:appuser /download /app

USER appuser

EXPOSE 8000

CMD ["python", "/app/app/app.py"]
