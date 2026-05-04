# 🍣 UMAMI Premium Sushi — To'liq Loyiha

## 📋 Tarkib

```
umami_final/
├── resturant/
│   ├── core/           # Django app (models, views, urls, admin)
│   ├── src/            # Sozlamalar (settings, urls, wsgi)
│   ├── templates/      # HTML shablonlar
│   │   ├── base.html       — Asosiy shablon
│   │   ├── asosiy.html     — Bosh sahifa
│   │   ├── menyu.html      — Menyu sahifasi
│   │   ├── cart.html       — Savat & buyurtma
│   │   ├── aksiyalar.html  — Aksiyalar
│   │   ├── filiallar.html  — Filiallar
│   │   └── tg_webapp.html  — Telegram Web App
│   ├── static/         # CSS, JS, rasmlar
│   ├── media/          # Yuklangan rasmlar
│   ├── bot.py          # Telegram bot
│   └── manage.py
├── requirements.txt
├── setup.sh            — Birinchi marta ishga tushirish
├── start_all.bat       — Barcha servislarni ishga tushirish (Windows)
├── stop_all.bat        — Barcha servislarni to'xtatish (Windows)
└── .gitignore
```

---

## 🚀 Tez boshlash

### Windows
```batch
start_all.bat
```

### Linux/Mac
```bash
chmod +x setup.sh start_bot.sh
./setup.sh
```

---

## 🤖 Bot funksiyalari

| Tugma | Funksiya |
|-------|----------|
| 🍣 Menyu | Kategoriyalar va taomlar |
| 🎁 Aksiyalar | Faol chegirmalar |
| 📍 Filiallar | Xarita bilan filiallar |
| 📦 Buyurtmalarim | Buyurtmalar tarixi (Bugun/Kecha/Hafta/Oy/Yil) |
| 📲 Buyurtma berish | Telegram Web App ochadi |
| 📞 Aloqa | Telefon va manzil |

### Admin komandalar
```
/orders  — Yangi buyurtmalarni ko'rish
/stats   — Statistika
```

---

## 📲 Telegram Web App

**Imkoniyatlar:**
- Premium dark dizayn
- Kategoriya bo'yicha filter
- Qidiruv
- Savatga qo'shish
- Filial tanlash
- To'lov usuli tanlash
- Buyurtma tarixi

---

## 🌐 Sayt sahifalari

| URL | Sahifa |
|-----|--------|
| `/` | Bosh sahifa |
| `/menyu/` | Menyu |
| `/cart/` | Savat |
| `/delivery/` | Yetkazib berish |
| `/aksiyalar/` | Aksiyalar |
| `/filiallar/` | Filiallar |
| `/tg-app/` | Telegram Web App |
| `/admin/` | Admin panel |

---

## 🔐 Admin panel

URL: `http://localhost:8000/admin`
Login: `admin`
Parol: `admin123`

---

## 📦 Kerakli paketlar

```
Django>=4.2
python-telegram-bot>=20.7
Pillow>=10.0.0
requests>=2.31.0
pytz>=2024.1
```

---

## Muammo yuz bersa:

1. Tokenlarni tekshiring
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
