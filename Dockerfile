FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Зависимости отдельным слоем — пересобираются только при изменении requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Непривилегированный пользователь
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/storage/photos/contractors \
    && chown -R app:app /app/storage

COPY --chown=app:app . .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

# Через sh: не зависит от бита +x (в dev-compose код монтируется с хоста)
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
CMD ["python", "main_webhook.py"]
