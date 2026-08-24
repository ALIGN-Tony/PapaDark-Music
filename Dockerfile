# PapaDark Music bot — used automatically by Railway (and any Docker host)
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libopus0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY music-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY music-bot/ ./

CMD ["python", "bot.py"]
