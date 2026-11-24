FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Runs fully offline: tests, generation, pixel verification, control agents, and the
# report (cached model responses in outputs/responses are re-scored, not re-queried).
CMD ["make", "all"]
