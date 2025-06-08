"""Celery entry‑point: schedules periodic poll of Kaspi, handles retries."""
from celery import Celery
from requests.exceptions import RequestException

from .settings import settings
from .reporter import process

# ----------------------------------------------------------------------------
celery_app = Celery(
    "kaspi", broker=settings.REDIS_URL, backend=settings.REDIS_URL
)

# Celery ≥5.3 выдаёт предупреждение — включаем явный retry on startup
celery_app.conf.broker_connection_retry_on_startup = True

# ----------------------------------------------------------------------------
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Register periodic task every *POLL_INTERVAL_MIN* minutes."""

    sender.add_periodic_task(
        settings.POLL_INTERVAL_MIN * 60,  # seconds
        run.s(),                          # signature без аргументов
        name="kaspi‑poll",
    )


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),            # любые исключения
    retry_backoff=True,                    # экспоненциальная 1‑2‑4‑8‑…
    retry_kwargs={"max_retries": 5},      # 5 раз → потом gives‑up
)
def run(self):
    """Single execution: fetch → update spreadsheet."""

    try:
        process()
    except RequestException as exc:
        # сетевые ошибки уже пойманы autoretry_for, но оставим лог
        self.retry(exc=exc)