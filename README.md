# 🌍 USGS Zilzilalar ETL — Bronze → Silver → Gold

Dunyodagi zilzilalar ma'lumotini [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)
dan **har kuni avtomatik** olib, medallion arxitektura bo'yicha kompyuterda saqlaydigan va
**Power BI uchun tayyor toza ma'lumot**ni OneDrive papkasiga yozadigan Python ETL pipeline.

```
 USGS API  ──►  🥉 BRONZE  ──►  🥈 SILVER  ──►  🥇 GOLD  ──►  📊 Power BI
 (GeoJSON)      xom JSON        toza Parquet     tayyor CSV     dashboard
                (kompyuter)     (kompyuter)      (OneDrive)
```

---

## 📌 Tezkor javoblar

| Savol | Javob |
|---|---|
| **Toza ma'lumotni qayerdan olaman?** | `OneDrive - Citifuel\PowerBI_data\earthquakes\` — 6 ta CSV (pastda ro'yxati) |
| **Kodni qayerdan ko'raman?** | GitHub: https://github.com/hamroali/usgs-earthquake-etl yoki VS Code'da `code D:\projects\etl-eia` |
| **Bronze / silver qayerda?** | `D:\projects\etl-eia\data\bronze\` va `data\silver\` (GitHub'ga yuklanmaydi) |
| **Qachon yangilanadi?** | Har kuni 08:00 da (Windows Task Scheduler → `USGS_Earthquake_ETL`) |
| **Power BI'da necha kunlik ma'lumot turadi?** | Oxirgi **365 kun** (sirpanuvchi oyna, `.env` dagi `GOLD_DAYS`) |
| **Ishladimi-yo'qmi qanday bilaman?** | `logs\etl.log` yoki Power BI'dagi `refresh_info.csv` → `last_refresh_tashkent` |

---

## 📁 Loyiha tuzilishi

```
etl-eia/
├── main.py              ← hammasini ketma-ket ishga tushiradi: bronze → silver → gold
├── run_etl.bat          ← Task Scheduler har kuni shuni ishga tushiradi
├── src/
│   ├── config.py        ← sozlamalar: papkalar, saqlash muddati, Markaziy Osiyo chegarasi
│   ├── bronze.py        ← API'dan olish (qayta urinish, incremental, bronze tozalash)
│   ├── silver.py        ← tozalash, boyitish, takrorlarni olib tashlash
│   └── gold.py          ← Power BI uchun jadvallar
├── data/                ← ⛔ GitHub'ga yuklanmaydi
│   ├── bronze/          ← 2026-11-17_034136_usgs_01.json ...
│   └── silver/          ← earthquakes.parquet
├── logs/                ← ⛔ GitHub'ga yuklanmaydi
│   ├── etl.log          ← har ishga tushirish: qator sonlari, sifat hisoboti, xatolar
│   ├── scheduler.log    ← Task Scheduler ishga tushirganda konsol chiqishi
│   └── state.json       ← oxirgi muvaffaqiyatli yuklash vaqti
├── .env                 ← ⛔ shaxsiy sozlamalar (GitHub'ga yuklanmaydi)
├── .env.example         ← .env uchun namuna
└── requirements.txt
```

---

## 🥉🥈🥇 Qatlamlar

### 🥉 Bronze — xom ma'lumot
- **Joyi:** `data\bronze\YYYY-MM-DD_HHMMSS_usgs_NN.json`
- API javobi **o'zgartirilmasdan** saqlanadi — biror narsa buzilsa, shu yerdan qayta tiklash mumkin.
- Har ishga tushirishda **yangi fayl** qo'shiladi (eskisi ustidan yozilmaydi).
- **Qanday ko'raman:** VS Code'da JSON faylni oching.

### 🥈 Silver — toza, to'liq tarix
- **Joyi:** `data\silver\earthquakes.parquet` (bitta fayl)
- Har zilzila = 1 qator, **takror yo'q** (bitta `event_id` uchun eng oxirgi versiya qoladi).
- Vaqt UTC va Toshkent vaqtida, mintaqa, magnituda/chuqurlik toifalari qo'shilgan.
- **Butun tarix saqlanadi** — hech narsa o'chirilmaydi.
- **Qanday ko'raman:**
  - Power BI: *Get Data → Parquet*
  - Python: `pd.read_parquet("data/silver/earthquakes.parquet")`

### 🥇 Gold — Power BI uchun tayyor
- **Joyi:** `OneDrive - Citifuel\PowerBI_data\earthquakes\`
- Faqat haqiqiy zilzilalar (portlash, karyer va h.k. chiqarilgan), **oxirgi 365 kun**.

| Fayl | Nima bor | Dashboard'da |
|---|---|---|
| `map_events.csv` | M2.5+ zilzilalar: koordinata, magnituda, chuqurlik, joy | 🗺 Xarita, filtrlar |
| `daily_summary.csv` | Kunlik soni, M2.5+/M5+ soni, o'rtacha/maks magnituda | 📈 Trend grafigi |
| `region_summary.csv` | Mintaqa bo'yicha soni va kuchi (M2.5+) | 🌏 Bar chart |
| `top_events.csv` | Eng kuchli 50 ta zilzila | 🏆 Jadval |
| `hourly_pattern.csv` | Soat (UTC) bo'yicha taqsimot | 🕐 Ustunli grafik |
| `refresh_info.csv` | Oxirgi yangilanish vaqti, ma'lumot oralig'i | 🔄 KPI kartochka |

> ⚠️ **Gold ustun nomlari va tartibi Power BI'ga bog'langan — o'zgartirmang.**

---

## 🔄 Har kuni nima bo'ladi?

1. **08:00** — Task Scheduler `run_etl.bat` ni ishga tushiradi.
2. **Bronze:** API'dan oxirgi yuklashdan beri **yangi qo'shilgan yoki tuzatilgan** zilzilalar olinadi
   (24 soat zaxira bilan). Yangi JSON fayl yoziladi.
   > USGS zilzilalarni keyin tuzatadi: avval `automatic`, seysmolog tekshirgach `reviewed`,
   > magnituda ham o'zgarishi mumkin. Shuning uchun faqat yangilarini emas, o'zgarganlarini ham olamiz.
3. **Silver:** yangi qatorlar eskilariga **qo'shiladi**; o'zgargan zilzila **yangilanadi** (takror bo'lmaydi).
4. **Gold:** CSV fayllar **to'liq qayta yoziladi** (qo'shilmaydi!) — har doim oxirgi 365 kun.
   Eng eski kun chiqib ketadi, bugungi kun qo'shiladi.
5. **Sifat hisoboti** `logs\etl.log` ga yoziladi.
6. **Power BI** refresh qilinganda yangi ma'lumotni ko'radi.

> 💡 Gold fayllar avval `.tmp` nomida yoziladi, keyin almashtiriladi — Power BI yarim yozilgan faylni o'qib qolmaydi.
> Agar biror bosqichda xato bo'lsa, `state.json` yangilanmaydi va ertangi ishga tushirish o'sha joydan davom etadi.

---

## 🗓 Saqlash muddati (retention)

| Qatlam | Qancha saqlanadi | O'zgartirish (`.env`) | Taxminiy hajm |
|---|---|---|---|
| 🥉 Bronze | Oxirgi 90 kun (eskilari avtomatik o'chiriladi) | `BRONZE_KEEP_DAYS=90` (0 = o'chirilmaydi) | ~45 MB (90 kun × ~0.5 MB) |
| 🥈 Silver | Butun tarix | — | ~9 MB / yil |
| 🥇 Gold | Oxirgi 365 kun | `GOLD_DAYS=730` → 2 yil | ~7 MB |

> Bronze tozalash faqat **silver muvaffaqiyatli yangilangandan keyin** ishlaydi, shuning uchun
> o'chirilgan JSON'dagi ma'lumot silver'da allaqachon bor bo'ladi.

---

## 🚀 Birinchi marta o'rnatish

```bash
git clone https://github.com/hamroali/usgs-earthquake-etl.git
cd usgs-earthquake-etl
pip install -r requirements.txt
copy .env.example .env
```
`.env` da `GOLD_DIR` ni o'z papkangizga moslang, keyin:
```bash
python main.py
```
Birinchi ishga tushirishda oxirgi 365 kun yuklanadi (~140 ming qator, ~1 daqiqa).
Keyingi ishga tushirishlar bir necha soniya oladi.

### Kunlik avtomatik ishga tushirish (Windows)
PowerShell'da:
```powershell
$a = New-ScheduledTaskAction -Execute "D:\projects\etl-eia\run_etl.bat" -WorkingDirectory "D:\projects\etl-eia"
$t = New-ScheduledTaskTrigger -Daily -At 08:00
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "USGS_Earthquake_ETL" -Action $a -Trigger $t -Settings $s -Force
```
Tekshirish: *Task Scheduler → USGS_Earthquake_ETL → o'ng tugma → Run*, keyin `logs\scheduler.log` ga qarang.

---

## 📊 Power BI'ga ulash

1. *Get Data → Text/CSV* → `PowerBI_data\earthquakes\` dagi fayllarni tanlang.
2. Xarita uchun `map_events` dan `latitude` / `longitude` ni **Map** yoki **Azure Map** visual'ga qo'ying,
   o'lcham → `magnitude`, rang → `depth_category`.
3. Power BI Service'da avtomatik refresh uchun fayllarni *SharePoint folder* (OneDrive for Business) orqali ulang —
   gateway kerak emas.

---

## 📖 Lug'at

| Ustun | Ma'nosi |
|---|---|
| `event_id` | Zilzilaning noyob ID'si (USGS) |
| `magnitude` | Kuchi (logarifmik: 6 = 5 dan ~32 marta kuchliroq energiya; kichiklari manfiy bo'lishi mumkin) |
| `mag_category` | `<3 kuchsiz`, `3-4.9 o'rtacha`, `5-6.9 kuchli`, `7+ juda kuchli` |
| `depth_km` / `depth_category` | O'chog'i chuqurligi: sayoz (<70), o'rta (70–300), chuqur (300+ km) |
| `time_utc` / `time_tashkent` | Sodir bo'lgan vaqt (Toshkent = UTC+5) |
| `region` | `place` matnidagi oxirgi qism — davlat yoki AQSh shtati |
| `is_central_asia` | Kenglik 35–56°, uzunlik 46–88° oralig'ida (taxminiy) |
| `status` | `automatic` yoki `reviewed` (seysmolog tekshirgan) |
| `sig` | USGS ahamiyatlilik bali (magnituda + sezilganlik + zarar) |
| `felt` | Nechta odam "sezdim" deb xabar bergan |
| `alert` | PAGER ogohlantirish darajasi: green / yellow / orange / red |
| `tsunami` | Okean mintaqasida bo'lganmi (tsunami bo'ldi degani emas) |

---

## 🛠 Muammo bo'lsa

| Holat | Yechim |
|---|---|
| Power BI'da ma'lumot yangilanmagan | `refresh_info.csv` dagi vaqtni va `logs\etl.log` oxirini tekshiring |
| `etl.log` da `XATO` | Xato matni o'sha yerda; internetni tekshirib, `python main.py` ni qayta ishga tushiring |
| Hammasini boshidan yuklash kerak | `logs\state.json` va `data\silver\earthquakes.parquet` ni o'chirib, `python main.py` |
| Kompyuter 08:00 da o'chiq edi | Vazifa yoqilgandan keyin bajariladi; o'tkazib yuborilgan kunlar keyingi ishga tushirishda olinadi |
