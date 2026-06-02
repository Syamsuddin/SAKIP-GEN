# Image produksi SAKIP-Gen (FastAPI + aiogram via gunicorn/UvicornWorker).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    BIND=0.0.0.0:8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Pengguna non-root
RUN useradd --system --uid 10001 sakipgen && chown -R sakipgen /app
USER sakipgen

EXPOSE 8000
# Healthcheck container (opsional; butuh curl di image → gunakan python)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"

CMD ["gunicorn", "app:app", "-c", "deploy/gunicorn.conf.py"]
