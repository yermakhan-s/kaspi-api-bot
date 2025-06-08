FROM python:3.11-slim

# CA‑certificates + curl → TLS и отладка внутри контейнера
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ← JSON‑form CMD в одну строку
CMD ["watchmedo", "auto-restart", "--recursive", "--pattern=*.py", "--", "python", "-m", "celery", "-A", "app.tasks", "worker", "--loglevel=info"]
