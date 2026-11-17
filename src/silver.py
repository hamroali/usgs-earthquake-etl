"""SILVER: bronze JSON -> tozalangan, boyitilgan jadval (har zilzila = 1 qator).

Yangi bronze yozuvlar mavjud silver bilan birlashtiriladi; bitta event_id uchun
eng oxirgi `updated` versiyasi qoladi (takror bo'lmaydi).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import CA_LAT, CA_LON, SILVER_DIR, get_logger

log = get_logger()
SILVER_FILE = SILVER_DIR / "earthquakes.parquet"

COLUMNS = [
    "event_id", "time_utc", "time_tashkent", "date", "hour", "magnitude", "mag_type",
    "mag_category", "depth_km", "depth_category", "latitude", "longitude", "place",
    "region", "is_central_asia", "event_type", "status", "sig", "tsunami", "felt",
    "alert", "url", "updated_utc",
]


def _flatten(files: list[Path]) -> pd.DataFrame:
    rows = []
    for f in files:
        for feat in json.loads(f.read_text(encoding="utf-8"))["features"]:
            p = feat["properties"]
            lon, lat, depth = (feat["geometry"]["coordinates"] + [None] * 3)[:3]
            rows.append({
                "event_id": feat["id"], "time": p.get("time"), "updated": p.get("updated"),
                "magnitude": p.get("mag"), "mag_type": p.get("magType"),
                "place": p.get("place"), "event_type": p.get("type"),
                "status": p.get("status"), "sig": p.get("sig"), "tsunami": p.get("tsunami"),
                "felt": p.get("felt"), "alert": p.get("alert"), "url": p.get("url"),
                "longitude": lon, "latitude": lat, "depth_km": depth,
            })
    return pd.DataFrame(rows)


def _region(place: pd.Series) -> pd.Series:
    # "7 km E of Calumet, Oklahoma" -> "Oklahoma"; "Fiji region" -> "Fiji region"
    r = place.fillna("Unknown").str.split(",").str[-1].str.strip()
    # "Japan Earthquake", "2025 Hubbard Glacier Earthquake", "Russia region" kabi nomlarni tozalash
    r = (r.str.replace(r"^\d{4}\s+", "", regex=True)
          .str.replace(r"\s+Earthquake$", "", regex=True)
          .str.replace(r"^(.+?)\s+region$", r"\1", regex=True))
    r = r.replace({"CA": "California", "MX": "Mexico", "Southern Alaska": "Alaska",
                   "Hubbard Glacier": "Alaska"})
    return r.where(r != "", "Unknown")


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["time_utc"] = pd.to_datetime(df["time"], unit="ms", utc=True).dt.tz_localize(None)
    df["updated_utc"] = pd.to_datetime(df["updated"], unit="ms", utc=True).dt.tz_localize(None)
    df["time_tashkent"] = df["time_utc"] + pd.Timedelta(hours=5)
    df["date"] = df["time_utc"].dt.date
    df["hour"] = df["time_utc"].dt.hour

    df["mag_category"] = pd.cut(df["magnitude"], [-np.inf, 3, 5, 7, np.inf], right=False,
                                labels=["<3 kuchsiz", "3-4.9 o'rtacha", "5-6.9 kuchli", "7+ juda kuchli"]
                                ).astype("string")
    df["depth_category"] = pd.cut(df["depth_km"], [-np.inf, 70, 300, np.inf], right=False,
                                  labels=["sayoz (<70 km)", "o'rta (70-300 km)", "chuqur (300+ km)"]
                                  ).astype("string")
    df["region"] = _region(df["place"])
    df["is_central_asia"] = (df["latitude"].between(*CA_LAT) & df["longitude"].between(*CA_LON))
    df["tsunami"] = df["tsunami"].fillna(0).astype(bool)
    df["felt"] = df["felt"].astype("Int64")
    df["sig"] = df["sig"].astype("Int64")
    return df[COLUMNS]


def run(bronze_files: list[Path]) -> tuple[pd.DataFrame, dict]:
    raw = _flatten(bronze_files)
    stats = {"bronze_rows": len(raw)}
    new = transform(raw) if len(raw) else pd.DataFrame(columns=COLUMNS)

    if SILVER_FILE.exists():
        old = pd.read_parquet(SILVER_FILE)
        stats["silver_before"] = len(old)
        combined = pd.concat([old, new], ignore_index=True)
    else:
        stats["silver_before"] = 0
        combined = new

    combined = (combined.sort_values("updated_utc")
                .drop_duplicates("event_id", keep="last")
                .dropna(subset=["time_utc", "latitude", "longitude"])
                .sort_values("time_utc")
                .reset_index(drop=True))
    combined["region"] = _region(combined["place"])  # qoida o'zgarsa, eski qatorlar ham yangilanadi
    stats["silver_after"] = len(combined)
    stats["new_or_updated"] = len(new)

    tmp = SILVER_FILE.with_suffix(".tmp")
    combined.to_parquet(tmp, index=False)
    tmp.replace(SILVER_FILE)
    log.info("Silver: bronze %s qator -> silver %s qator (avval %s)",
             stats["bronze_rows"], stats["silver_after"], stats["silver_before"])
    return combined, stats
