"""Umumiy sozlamalar: papkalar, API manzili, log."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"
LOG_DIR = ROOT / "logs"
STATE_FILE = LOG_DIR / "state.json"

# Gold qatlam Power BI o'qiydigan papkaga yoziladi (.env dagi GOLD_DIR)
GOLD_DIR = Path(os.getenv("GOLD_DIR", ROOT / "data" / "gold"))

API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
HISTORY_DAYS = int(os.getenv("HISTORY_DAYS", "365"))  # birinchi yuklashda necha kun
# Saqlash muddati (retention)
GOLD_DAYS = int(os.getenv("GOLD_DAYS", "365"))              # Power BI'da oxirgi necha kun turadi
BRONZE_KEEP_DAYS = int(os.getenv("BRONZE_KEEP_DAYS", "0"))  # 0 = bronze fayllar o'chirilmaydi

OVERLAP_HOURS = 24         # incremental yuklashda zaxira (tuzatilgan zilzilalar uchun)
MAP_MIN_MAG = 2.5           # xaritaga chiqadigan minimal magnituda

# Markaziy Osiyo chegarasi (taxminiy to'rtburchak)
CA_LAT = (35.0, 56.0)
CA_LON = (46.0, 88.0)

for d in (BRONZE_DIR, SILVER_DIR, LOG_DIR, GOLD_DIR):
    d.mkdir(parents=True, exist_ok=True)


def get_logger() -> logging.Logger:
    log = logging.getLogger("etl")
    if not log.handlers:
        log.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh = logging.FileHandler(LOG_DIR / "etl.log", encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(fh)
        log.addHandler(sh)
    return log
