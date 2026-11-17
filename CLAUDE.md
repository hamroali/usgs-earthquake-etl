# Loyiha: USGS Zilzilalar ETL

**Avval `D:\projects\_kit\etl-rules.md` ni o'qi va unga amal qil.**

## Asosiy ma'lumot
- Maqsad: USGS API'dan dunyo zilzilalarini har kuni olib, Power BI dashboard uchun tayyorlash
- Rejim: ETL (Python + pandas), medallion arxitektura: bronze → silver → gold
- Soha: yo'q (o'quv / portfolio loyihasi)

## Manba
- Turi: API (GeoJSON)
- Manzil yoki hujjat: https://earthquake.usgs.gov/fdsnws/event/1/
- Kalit: kerak emas
- Yangilanish: kunlik (Task Scheduler → `run_etl.bat`), incremental `updatedafter` bilan

## Natija
- Format: CSV (gold), Parquet (silver), JSON (bronze)
- Joyi: gold → `.env` dagi `GOLD_DIR` (OneDrive `PowerBI_data\earthquakes\`); bronze/silver → `data/`
- Kerakli ustunlar: `src/gold.py` dagi tartib — o'zgartirma
- Kim ishlatadi: Power BI dashboard

## Lug'at
README.md ga qara.

## Qo'shimcha qoidalar
- Papka nomlari etl-rules.md dan farqli: raw=bronze, clean=silver, output=gold (foydalanuvchi so'rovi).
- USGS zilzilalarni keyin tuzatadi — incremental yuklash 24 soat zaxira bilan olinadi, silver'da event_id bo'yicha oxirgi `updated` qoladi.
- `updatedbefore` parametri API'da yo'q.
- Retention: gold = oxirgi `GOLD_DAYS` (365) kun, CSV har safar to'liq qayta yoziladi; silver = butun tarix;
  bronze = `BRONZE_KEEP_DAYS` (0 = o'chirilmaydi; yoqishdan oldin foydalanuvchidan so'ra).
- GitHub: https://github.com/hamroali/usgs-earthquake-etl
