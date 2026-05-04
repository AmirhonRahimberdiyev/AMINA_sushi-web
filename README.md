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
│   │   └── tg_webapp.html  — Telegram Web App (YANGI!)
│   ├── static/         # CSS, JS, rasmlar
│   ├── media/          # Yuklangan rasmlar
│   ├── bot.py          # Telegram bot (YANGILANGAN!)
│   ├── .env            # Token va sozlamalar
│   └── manage.py
├── requirements.txt
├── setup.sh            — Birinchi marta ishga tushirish
├── start_server.sh     — Django server
└── start_bot.sh        — Telegram bot
```

---

## 🚀 Tez boshlash

### 1. O'rnatish
```bash
cd umami_final
chmod +x setup.sh start_server.sh start_bot.sh
./setup.sh
```

### 2. Server ishga tushirish (1-terminal)
```bash
./start_server.sh
```

### 3. Bot ishga tushirish (2-terminal)
```bash
./start_bot.sh
```

---

## ⚙️ Sozlamalar (`.env`)

```env
BOT_TOKEN=8714192126:AAGBazzW_xPuk6pT5eT5gNbOKnlx0R278eM
BOT_CHAT_ID=6830116501
ADMIN_CHAT_ID=6830116501
BOT_USERNAME=amina_suhsi_order_bot
SITE_URL=http://localhost:8000   ← Production da o'zgartiring!
```

> ⚠️ **MUHIM**: Telegram Web App ishlatish uchun HTTPS kerak bo'ladi!
> Production da `SITE_URL=https://sizningsayt.uz` deb yozing.

---

## 🤖 Bot funksiyalari

| Tugma | Funksiya |
|-------|----------|
| 🍣 Menyu | Kategoriyalar va taomlar |
| 🎁 Aksiyalar | Faol chegirmalar |
| 📍 Filiallar | Xarita bilan filiallar |
| 📲 Buyurtma berish | **Telegram Web App** ochadi |
| 📞 Aloqa | Telefon va manzil |

### Admin komandalar
```
/orders  — Yangi buyurtmalarni ko'rish
/stats   — Statistika (buyurtmalar, foydalanuvchilar)
```

### Yangi buyurtma kelganda admin quyidagini oladi:
```
🍣 YANGI BUYURTMA #42

👤 Ali Valiyev
📞 +998901234567
📍 Chilonzor, 12-kvartal, 5-uy

🛒 Buyurtma:
  • Salmon Roll — 65,000 so'm
  • Nigiri Set — 95,000 so'm

💰 Jami: 160,000 so'm
💳 Click
📌 Telegram Web App
🕐 15.05.2026 14:30

[✅ Tasdiqlash] [❌ Bekor]
```

---

## 📲 Telegram Web App

Web App manzili: `http://yourdomain.com/tg-app/`

**Imkoniyatlar:**
- Premium dark dizayn
- Kategoriya bo'yicha filter
- Qidiruv
- Savatga qo'shish va miqdor boshqaruvi
- Foydalanuvchi ma'lumotlari avtomatik to'ldirish (Telegram'dan)
- To'lov usuli tanlash (Naqd/Karta/Click/Payme)
- Buyurtma tasdiqlanganda Telegram orqali bildirishnoma

---

## 🌐 Sayt sahifalari

| URL | Sahifa |
|-----|--------|
| `/` | Bosh sahifa |
| `/menyu/` | Menyu |
| `/cart/` | Savat va buyurtma |
| `/aksiyalar/` | Aksiyalar |
| `/filiallar/` | Filiallar |
| `/tg-app/` | Telegram Web App |
| `/admin/` | Admin panel |

---

## 🔐 Admin panel

URL: `http://localhost:8000/admin`
Login: `admin`
Parol: `admin123`

Admin panelda:
- Buyurtmalarni boshqarish va status o'zgartirish
- Taomlar va kategoriyalar qo'shish/tahrirlash
- Aksiyalar yaratish
- Filiallarni boshqarish
- Telegram foydalanuvchilarni ko'rish

---

## 🏭 Production uchun (Server deploy)

### Nginx + Gunicorn

```bash
pip install gunicorn
gunicorn src.wsgi:application --workers 3 --bind 0.0.0.0:8000
```

### .env ni yangilash
```env
SITE_URL=https://sizningsayt.uz
```

### Webhook o'rnatish (ixtiyoriy)
```bash
curl "https://api.telegram.org/bot8714192126:AAGBazzW_xPuk6pT5eT5gNbOKnlx0R278eM/setWebhook?url=https://sizningsayt.uz/webhook/"
```

---

## 📦 Kerakli paketlar

```
Django>=4.2,<5.0
python-telegram-bot==20.7
Pillow>=10.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

---

## 📞 Yordam kerakmi?

Muammo yuz bersa:
1. `.env` faylidagi token to'g'riligini tekshiring
2. `pip install -r requirements.txt` ni qaytadan bajaring
3. `python manage.py migrate` ni bajaring
