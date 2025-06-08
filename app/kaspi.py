"""Kaspi API v2 — incremental order fetcher."""
from __future__ import annotations
import logging, time, socket
from typing import List, Dict

import requests
from urllib3.util import connection as urllib3_conn

from .settings import settings, ACTIVE_STATUSES
from .state import read_since_ts, write_since_ts

log = logging.getLogger(__name__)

API_BASE = "https://kaspi.kz/shop/api/v2"
PAGE_SIZE = 50
REQ_TIMEOUT = (5, 40)  # (connect, read)

# IPv4 only (Kaspi IPv6 бывает недоступен)
urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

HEADERS = {
    "User-Agent": "PostmanRuntime/7.39.0",
    "Content-Type": "application/vnd.api+json",
    "Accept": "application/vnd.api+json",
    "X-Auth-Token": settings.KASPI_TOKEN,
}

# ────────────────────────────────────────────────────────────────────

def _fetch_page(state: str, date_ge: int, date_le: int, page: int) -> List[Dict]:
    params = {
        "filter[orders][state]": state,
        "filter[orders][creationDate][$ge]": date_ge,
        "filter[orders][creationDate][$le]": date_le,
        "page[number]": page,
        "page[size]": PAGE_SIZE,
    }
    resp = requests.get(f"{API_BASE}/orders", headers=HEADERS,
                        params=params, timeout=REQ_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("data", [])

# ────────────────────────────────────────────────────────────────────

def fetch_active_orders() -> List[Dict]:
    """Fetch new/updated orders since last poll, never >14 days window."""

    now_ms   = int(time.time()*1000)
    start_ms = read_since_ts(default=0)

    # Sliding windows (3 д → 1 д) to avoid huge responses
    windows_days = [3, 1]
    collected: List[Dict] = []

    for days in windows_days:
        max_ms = days*24*60*60*1000
        while start_ms < now_ms:
            end_ms = min(start_ms+max_ms, now_ms)
            for state in ACTIVE_STATUSES:
                page = 0
                while True:
                    chunk = _fetch_page(state, start_ms, end_ms, page)
                    if not chunk:
                        break
                    collected.extend(chunk)
                    page += 1
                    if len(chunk) < PAGE_SIZE:
                        break
            if end_ms >= now_ms:
                break
            start_ms = end_ms

    newest = max((int(o["attributes"]["creationDate"]) for o in collected),
                 default=now_ms) + 1
    write_since_ts(newest)

    log.info("Kaspi: fetched %d orders", len(collected))
    return collected