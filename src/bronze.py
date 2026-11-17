"""BRONZE: USGS API'dan xom ma'lumotni olib, o'zgartirmasdan JSON qilib saqlash.

- Birinchi marta: oxirgi HISTORY_DAYS kun, 30 kunlik bo'laklarda (API limiti 20 000).
- Keyingi safar: `updatedafter` = oxirgi yuklash - 24 soat. Shunda yangilar ham,
  keyin tuzatilgan (magnitudasi/statusi o'zgargan) zilzilalar ham keladi.
"""
import json
import time
from datetime import datetime, timedelta, timezone

import requests

from .config import (API_URL, BRONZE_DIR, HISTORY_DAYS, OVERLAP_HOURS,
                     STATE_FILE, get_logger)

log = get_logger()
API_LIMIT = 20000


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _get(params: dict) -> dict:
    """So'rov: timeout, 3 marta qayta urinish, keyin aniq xato."""
    params = {"format": "geojson", "orderby": "time-asc", **params}
    last_err = None
    for attempt in range(1, 4):
        try:
            r = requests.get(API_URL, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            last_err = e
            resp = getattr(e, "response", None)
            if resp is not None and 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise RuntimeError(f"USGS API so'rovni rad etdi ({resp.status_code}): {resp.text[:300]}") from e
            log.warning("API xato (urinish %s/3): %s", attempt, e)
            time.sleep(5 * attempt)
    raise RuntimeError(f"USGS API 3 urinishdan keyin ham javob bermadi: {last_err}")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _windows(start: datetime, end: datetime, days: int):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def _fetch_window(start: datetime, end: datetime) -> list:
    """Zilzila vaqti bo'yicha oraliq; limitga yetsa, ikkiga bo'lib qayta oladi."""
    feats = _get({"starttime": _iso(start), "endtime": _iso(end)})["features"]
    if len(feats) >= API_LIMIT and end - start > timedelta(hours=1):
        mid = start + (end - start) / 2
        return _fetch_window(start, mid) + _fetch_window(mid, end)
    return feats


def _fetch_updated(updated_after: datetime, now: datetime) -> list:
    """Oxirgi yuklashdan keyin qo'shilgan YOKI tuzatilgan zilzilalar
    (oxirgi HISTORY_DAYS kun ichida sodir bo'lganlari)."""
    feats = _get({"updatedafter": _iso(updated_after),
                  "starttime": _iso(now - timedelta(days=HISTORY_DAYS)),
                  "endtime": _iso(now)})["features"]
    if len(feats) >= API_LIMIT:
        raise RuntimeError("Incremental so'rov 20 000 limitiga yetdi — "
                           "logs/state.json ni o'chirib, to'liq qayta yuklang.")
    return feats


def run() -> tuple[list, dict]:
    """Yangi bronze fayllar va yangilangan state'ni qaytaradi.
    State faqat butun pipeline muvaffaqiyatli tugagach saqlanadi (main.py)."""
    state = load_state()
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    files = []

    if "last_run_utc" not in state:
        start = now - timedelta(days=HISTORY_DAYS)
        log.info("Birinchi yuklash: %s dan %s gacha", start.date(), now.date())
        key, chunks = "starttime", list(_windows(start, now, 30))
    else:
        start = datetime.fromisoformat(state["last_run_utc"]) - timedelta(hours=OVERLAP_HOURS)
        log.info("Incremental yuklash: %s dan keyin qo'shilgan/o'zgarganlar", start)
        key, chunks = "updatedafter", [(start, now)]

    for i, (s, e) in enumerate(chunks, 1):
        feats = _fetch_window(s, e) if key == "starttime" else _fetch_updated(s, now)
        path = BRONZE_DIR / f"{stamp}_usgs_{i:02d}.json"
        payload = {"extracted_at_utc": _iso(now), "query": {key: _iso(s), "end": _iso(e)},
                   "type": "FeatureCollection", "features": feats}
        path.write_text(json.dumps(payload), encoding="utf-8")
        files.append(path)
        log.info("Bronze [%s/%s] %s -> %s: %s ta yozuv -> %s",
                 i, len(chunks), s.date(), e.date(), len(feats), path.name)

    return files, {**state, "last_run_utc": _iso(now)}
