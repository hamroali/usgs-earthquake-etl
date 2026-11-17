"""USGS zilzilalar ETL: bronze -> silver -> gold.

Ishga tushirish:  python main.py
"""
import sys
import time

import pandas as pd

from src import bronze, gold, silver
from src.config import get_logger

log = get_logger()


def quality_report(df: pd.DataFrame, stats: dict, gold_rows: dict) -> None:
    dates = pd.to_datetime(df["date"])
    all_days = pd.date_range(dates.min(), dates.max(), freq="D")
    missing_days = all_days.difference(dates.unique())
    nulls = df[["magnitude", "depth_km", "place"]].isna().sum().to_dict()

    log.info("---- SIFAT HISOBOTI ----")
    log.info("Bronze (API dan kelgan): %s | Silver: %s (avval %s) | Takror event_id: %s",
             stats["bronze_rows"], stats["silver_after"], stats["silver_before"],
             df["event_id"].duplicated().sum())
    log.info("Gold: %s", gold_rows)
    log.info("Sana oralig'i: %s .. %s | Ma'lumotsiz kunlar: %s",
             dates.min().date(), dates.max().date(),
             [d.date().isoformat() for d in missing_days] or "yo'q")
    log.info("Bo'sh qiymatlar: %s", nulls)
    log.info("Hodisa turlari: %s", df["event_type"].value_counts().to_dict())


def main() -> int:
    t0 = time.time()
    log.info("==== ETL boshlandi ====")
    try:
        files, new_state = bronze.run()
        df, stats = silver.run(files)
        gold_rows = gold.build(df)
        bronze.save_state(new_state)  # faqat hammasi muvaffaqiyatli bo'lsa
        quality_report(df, stats, gold_rows)
    except Exception:
        log.exception("ETL XATO bilan tugadi")
        return 1
    log.info("==== ETL tugadi: %.1f soniya ====", time.time() - t0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
