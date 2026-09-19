# Fase 7, T-7.8. Base disamakan dengan runtime pembuat artefak
# (MANIFEST.json -> environment.python = 3.12.3).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Kode saja. Artefak model (±9 MB) dan cache stem (±600 KB) TIDAK disalin —
# keduanya di-mount read-only lewat docker-compose, sehingga image tetap ramping
# dan melatih ulang model tidak menuntut image dibangun ulang.
COPY api/         ./api/
COPY ml/__init__.py  ./ml/__init__.py
COPY ml/config.yaml  ./ml/config.yaml
COPY ml/src/      ./ml/src/

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
