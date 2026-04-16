# EduFlow — Django (PARVEZ EDUCATION)

O'quv markaz boshqaruv tizimi. **EduFlow** — **PARVEZ EDUCATION** dizayni: ko'k-binafsha rang, professional UI.

## Ishga tushirish

```bash
# 1. PostgreSQL yaratish
createdb scholarly_db

# 2. O'rnatish
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt

# 3. .env sozlash
cp .env.example .env
# .env faylda DB_PASSWORD ni o'zgartiring

# 4. Migratsiya + Demo ma'lumotlar
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data

# 5. Ishga tushirish
python manage.py runserver
```

**Brauzerda:** `http://localhost:8000`

## Docker orqali ishga tushirish

```bash
# 1) .env tayyorlash
cp .env.example .env
# Windows (PowerShell): copy .env.example .env

# 2) Konteynerlarni build + run
docker compose up --build
```

`docker-compose.yml` ichida:
- `web` — Django + Gunicorn (`:8000`)
- `db` — PostgreSQL (`:5432`)

Foydali buyruqlar:

```bash
# fon rejimida
docker compose up -d

# loglar
docker compose logs -f web

# konteyner ichida management command
docker compose exec web python manage.py createsuperuser

# to'xtatish
docker compose down
```

## Login
| Login   | Parol    | Rol           |
|---------|----------|---------------|
| admin   | admin123 | Administrator |
| sardor  | teach123 | O'qituvchi (Ingliz tili) |
| dilnoza | teach123 | O'qituvchi (Matematika) |

## Sahifalar
| URL | Tavsif |
|-----|--------|
| `/` | Dashboard |
| `/login/` | Kirish (rol kartochkalarsiz) |
| `/groups/` | Guruhlar (karta ko'rinish) |
| `/groups/<id>/` | Guruh detail + davomat |
| `/students/` | Talabalar (to'liq manzil) |
| `/teachers/` | O'qituvchilar |
| `/finance/` | Moliya |
| `/reports/` | Hisobotlar |
| `/messaging/` | SMS (admin) |

## SMS sozlash
`.env` da `SMS_BACKEND`:
- **dry_run** — forma ishlaydi, xabar tarmoqqa chiqmaydi (standart).
- **console** — har bir SMS `logging` orqali konsolga yoziladi.
- **webhook** — `SMS_WEBHOOK_URL` ga JSON: `{"phones": ["..."], "message": "..."}`. Ixtiyoriy `SMS_WEBHOOK_SECRET` sarlavha `X-Webhook-Secret`.

## Xususiyatlar
- Login sahifasi: chap ko'k panel + o'ng forma (rol kartochkasiz)
- Talaba qo'shishda: Viloyat → Tuman → Mahalla → Ko'cha → Uy → Kvartira → Qavat → Pochta indeksi
- Davomat: **sababli / sababsiz** — ketma-ket **Keldi → sababsiz kelmadi (to‘lov yo‘q) → sababli kelmadi (to‘lov bor) → Keldi**. «Hamma sababsiz kelmadi» — barchasi sababsiz deb belgilanadi.
- Moliya: balans avtomatik o'zgaradi
- Hisobot eksporti: **guruh** (ixtiyoriy) + **talaba** (ixtiyoriy): barcha tizim, faqat guruh, yoki bitta o‘quvchi. **Excel/CSV**, **Yo'qlama** varag‘i filtrga mos.
