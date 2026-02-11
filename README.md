# Інтелектуальна система оцінки рейтингу товарів та виробників (MVP)

MVP-проєкт для:
- збору **URL товарів** з категорій Rozetka
- збору **відгуків + рейтингу + даних товару**
- збереження результатів у **PostgreSQL**
- аналіз та створення рейтингу

Проєкт розділений на **скрипти збору** та **API-сервіс**.

---

## 📁 Структура проєкту

test_scraping/
│
├── app_v2.py # FastAPI сервіс: збір відгуків і запис у БД
├── collect_category_urls.py # Збір URL товарів з категорії Rozetka (Playwright)
├── run_range_to_db.py # Batch-запуск: відправка URL у API
├── product_urls.json # Список зібраних URL товарів
│
├── init_profile.py # Прогрів Playwright-профілю (Cloudflare)
├── pw_profile/ # Persistent browser profile (cookies, CF)
│
└── README.md


---

## 🧠 Архітектура

[ Rozetka category ]
↓
collect_category_urls.py
↓
product_urls.json
↓
run_range_to_db.py ──► FastAPI (app_v2.py)
↓
PostgreSQL


- **Playwright** використовується тільки там, де потрібен JS
- **FastAPI** — єдина точка запису в БД
- **PostgreSQL** — основне сховище

---

## ⚙️ Вимоги

- Python **3.10+**
- PostgreSQL **14+**
- Google Chrome (або Chromium)
- Windows / Linux / macOS

Python-пакети:
```bash
pip install fastapi uvicorn playwright bs4 psycopg requests
playwright install
🗄️ База даних
Приклад DSN
postgresql://reviews_user:STRONG_PASSWORD@localhost:5432/reviews_db
Змінна середовища:

$env:DB_DSN="postgresql://reviews_user:YOUR_PASSWORD@localhost:5432/reviews_db"


🚀 Крок 1. Прогрів Cloudflare (обовʼязково 1 раз)
python init_profile.py
відкриється браузер

пройди Cloudflare / captcha вручну

закрий браузер

Профіль збережеться у pw_profile/.

🚀 Крок 2. Запуск API
uvicorn app_v2:app --host 0.0.0.0 --port 8000
Перевір:

http://localhost:8000/health

http://localhost:8000/docs

Endpoint для збору в БД:

POST /fetch/rozetka/to_db

🚀 Крок 3. Збір URL товарів з категорії
Приклад для категорії Зарядні станції:

python collect_category_urls.py
Результат:

product_urls.json
Формат:

[
  "https://rozetka.com.ua/ua/365360001/p365360001/",
  "https://rozetka.com.ua/ua/364123456/p364123456/"
]
✔️ URL вже очищені від /comments/
✔️ Без дублікатів

🚀 Крок 4. Batch-збір і запис у БД
Запуск з інтервалом:

$env:ROZETKA_API_URL="http://localhost:8000/fetch/rozetka/to_db"
python run_range_to_db.py --start 1 --end 20 --sleep 2
Параметри:

--start — початковий індекс у product_urls.json

--end — кінцевий (не включно)

--sleep — пауза між запитами (сек)

Приклад логів:

[1] OK  https://rozetka.com.ua/ua/365360001/p365360001/
[2] OK  https://rozetka.com.ua/ua/364123456/p364123456/
DONE ok=2 fail=0
📦 Що зберігається в БД
products
title
brand
sku
description_html
description_text
specs_json
rating_avg
reviews_count
reviews
rating (1–5)
text / pros / cons
review_date
source_url

🧯 Типові проблеми
404 Not Found
перевір endpoint: /fetch/rozetka/to_db
перевір ROZETKA_API_URL

Cloudflare challenge
повторно запусти init_profile.py

не використовуй headless=True для першого запуску

Нема brand / sku
не всі сторінки Rozetka їх публікують

fallback: береться з JSON-LD або specs

🧩 Подальші покращення (roadmap)
⏸ resume batch-збору

🔁 дедуп відгуків

📊 агрегований рейтинг по категоріях

🧠 sentiment analysis (BERT)

🌐 web-інтерфейс



