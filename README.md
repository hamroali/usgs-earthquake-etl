# USGS Zilzilalar ETL (Bronze → Silver → Gold)

USGS Earthquake API'dan dunyodagi zilzilalarni har kuni olib, medallion arxitektura
bo'yicha kompyuterda saqlaydi va Power BI uchun tayyor CSV'larni OneDrive papkasiga yozadi.

## Ishga tushirish

```bash
pip install -r requirements.txt
copy .env.example .env     # GOLD_DIR ni o'zingizga moslang
python main.py
```

- **Birinchi marta**: oxirgi 365 kun yuklanadi (~140 ming qator, ~1 daqiqa).
- **Keyingi safar**: faqat oxirgi yuklashdan beri qo'shilgan **yoki tuzatilgan** zilzilalar (bir necha soniya).
- **Har kuni avtomatik**: Windows Task Scheduler → `USGS_Earthquake_ETL` vazifasi `run_etl.bat` ni ishga tushiradi.

## Qatlamlar

| Qatlam | Joyi | Nima bor |
|---|---|---|
| 🥉 Bronze | `data/bronze/YYYY-MM-DD_HHMMSS_usgs_NN.json` | API javobi, o'zgartirilmagan |
| 🥈 Silver | `data/silver/earthquakes.parquet` | Tozalangan, har zilzila 1 qator, takrorsiz |
| 🥇 Gold | `GOLD_DIR` (OneDrive `PowerBI_data/earthquakes/`) | Power BI uchun CSV jadvallar |

### Gold jadvallar
| Fayl | Tavsif |
|---|---|
| `map_events.csv` | M2.5+ zilzilalar (xarita uchun: latitude/longitude) |
| `daily_summary.csv` | Kunlik soni, M2.5+/M5+ soni, o'rtacha/maks magnituda |
| `region_summary.csv` | Mintaqalar bo'yicha (M2.5+) |
| `top_events.csv` | Eng kuchli 50 ta zilzila |
| `hourly_pattern.csv` | Soat (UTC) bo'yicha taqsimot |

> ⚠️ Gold ustun nomlari va tartibi Power BI'ga bog'langan — o'zgartirmang.

## Lug'at
- `magnitude` — zilzila kuchi (Rixter shkalasiga o'xshash, logarifmik; manfiy bo'lishi mumkin)
- `depth_km` — o'chog'i chuqurligi, km
- `time_utc` / `time_tashkent` — sodir bo'lgan vaqt (Toshkent = UTC+5)
- `status` — `automatic` (avtomatik) yoki `reviewed` (seysmolog tekshirgan)
- `sig` — USGS ahamiyatlilik bali (magnituda + sezilganlik + zarar)
- `is_central_asia` — kenglik 35–56°, uzunlik 46–88° oralig'ida
- `region` — `place` matnidagi oxirgi qism (davlat yoki AQSh shtati)

## Loglar
- `logs/etl.log` — har ishga tushirish, qator sonlari, sifat hisoboti, xatolar
- `logs/state.json` — oxirgi muvaffaqiyatli yuklash vaqti (o'chirilsa, to'liq qayta yuklanadi)
