"""GOLD: silver jadvaldan Power BI uchun tayyor jadvallar (CSV, OneDrive papkasiga).

Fayllar avval .tmp ga yoziladi, keyin almashtiriladi — Power BI/OneDrive
yarim yozilgan faylni o'qib qolmasligi uchun. Ustun nomlari va tartibi o'zgarmaydi.
"""
import pandas as pd

from .config import GOLD_DIR, MAP_MIN_MAG, get_logger

log = get_logger()


def _write(df: pd.DataFrame, name: str) -> None:
    path = GOLD_DIR / f"{name}.csv"
    tmp = GOLD_DIR / f"{name}.csv.tmp"
    df.to_csv(tmp, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d %H:%M:%S")
    tmp.replace(path)
    log.info("Gold: %-16s %6s qator -> %s", name, len(df), path)


def build(silver: pd.DataFrame) -> dict:
    eq = silver[silver["event_type"] == "earthquake"]

    map_events = eq[eq["magnitude"] >= MAP_MIN_MAG][[
        "event_id", "time_utc", "time_tashkent", "date", "magnitude", "mag_category",
        "depth_km", "depth_category", "latitude", "longitude", "place", "region",
        "is_central_asia", "sig", "tsunami", "felt", "alert", "status", "url"]]

    daily = (eq.groupby("date")
             .agg(quakes_total=("event_id", "count"),
                  quakes_m25_plus=("magnitude", lambda m: (m >= 2.5).sum()),
                  quakes_m5_plus=("magnitude", lambda m: (m >= 5).sum()),
                  avg_magnitude=("magnitude", "mean"),
                  max_magnitude=("magnitude", "max"),
                  avg_depth_km=("depth_km", "mean"))
             .round(2).reset_index())

    region = (eq[eq["magnitude"] >= MAP_MIN_MAG].groupby("region")
              .agg(quakes=("event_id", "count"),
                   avg_magnitude=("magnitude", "mean"),
                   max_magnitude=("magnitude", "max"),
                   avg_depth_km=("depth_km", "mean"),
                   last_quake_utc=("time_utc", "max"))
              .round({"avg_magnitude": 2, "avg_depth_km": 2}).sort_values("quakes", ascending=False).reset_index())

    top = (eq.nlargest(50, "magnitude")[[
        "event_id", "time_utc", "magnitude", "depth_km", "place", "region",
        "latitude", "longitude", "tsunami", "alert", "url"]].reset_index(drop=True))
    top.insert(0, "rank", range(1, len(top) + 1))

    hourly = (eq.groupby("hour").agg(quakes=("event_id", "count"),
                                     avg_magnitude=("magnitude", "mean"))
              .round(2).reindex(range(24), fill_value=0).rename_axis("hour_utc").reset_index())

    tables = {"map_events": map_events, "daily_summary": daily, "region_summary": region,
              "top_events": top, "hourly_pattern": hourly}
    for name, df in tables.items():
        _write(df, name)
    return {k: len(v) for k, v in tables.items()}
