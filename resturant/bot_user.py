#!/usr/bin/env python
"""
UMAMI Premium Sushi — Foydalanuvchi Bot (Mijozlar uchun)
Bot: @amina_suhsi_order_bot
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
django.setup()

from django.conf import settings as dj_settings
from asgiref.sync import sync_to_async
import logging

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

from core.models import Meal, Category, Branch, Aksiya, TelegramUser

logging.basicConfig(
    format='%(asctime)s — [USER BOT] — %(levelname)s — %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = dj_settings.USER_BOT_TOKEN
SITE_URL = dj_settings.SITE_URL

# ── Helpers ─────────────────────────────────────────────────────
@sync_to_async
def _get_or_create_tg_user(tg_id, username, first_name):
    return TelegramUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={'username': username, 'first_name': first_name}
    )

@sync_to_async
def _get_active_categories():
    return list(Category.objects.filter(is_active=True).order_by('id'))

@sync_to_async
def _get_category(cat_id):
    return Category.objects.get(id=cat_id)

@sync_to_async
def _get_meals_for_category(cat_id):
    return list(Meal.objects.filter(ctg_id=cat_id).prefetch_related('images')[:12])

@sync_to_async
def _get_meal(meal_id):
    return Meal.objects.get(id=meal_id)

@sync_to_async
def _get_branches():
    return list(Branch.objects.select_related('manager').all())

@sync_to_async
def _get_active_aksiyalar():
    return list(Aksiya.objects.filter(is_active=True).select_related('meal'))


# ── Klaviaturalar ─────────────────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🛒 Buyurtma berish", web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/"))],
        [KeyboardButton("🍣 Menyu"), KeyboardButton("🎁 Aksiyalar")],
        [KeyboardButton("📍 Filiallar"), KeyboardButton("💬 Kassir bilan chat")],
        [KeyboardButton("📞 Aloqa")],
        [KeyboardButton("ℹ️ Bot haqida")],
    ], resize_keyboard=True)


# ── Handlers ─────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await _get_or_create_tg_user(user.id, user.username, user.first_name)

    text = (
        f"🍣 <b>UMAMI Premium Sushi</b> ga xush kelibsiz!\n\n"
        f"Salom, <b>{user.first_name}</b>! 👋\n\n"
        f"🏆 Toshkentdagi eng yaxshi premium sushi restorani.\n"
        f"Har bir taom — san'at asari.\n\n"
        f"👇 Buyurtma berish uchun quyidagi tugmani bosing:"
    )

    if SITE_URL.startswith("https"):
        webapp_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🛒 Buyurtma berish — Mini App",
                web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/")
            )
        ]])
        await update.message.reply_html(text, reply_markup=webapp_kb)
    else:
        url_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🛒 Buyurtma berish (saytni ochish)",
                url=f"{SITE_URL}/tg-app/"
            )
        ]])
        await update.message.reply_html(text, reply_markup=url_kb)

    await update.message.reply_text(
        "📋 Boshqa bo'limlar:",
        reply_markup=main_keyboard()
    )


async def menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    categories = await _get_active_categories()
    if not categories:
        await update.message.reply_html("😕 Hozircha menyu mavjud emas.")
        return

    cats_icons = {"sushi": "🍣", "roll": "🌯", "set": "🍱", "salat": "🥗",
                  "ichimlik": "🥤", "desert": "🍮", "sup": "🍜"}

    keyboard = []
    for cat in categories:
        icon = "🍽"
        for k, v in cats_icons.items():
            if k in cat.name.lower():
                icon = v
                break
        keyboard.append([InlineKeyboardButton(
            f"{icon} {cat.name}",
            callback_data=f"cat_{cat.id}"
        )])

    keyboard.append([InlineKeyboardButton(
        "🛒 Web App orqali buyurtma",
        web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/")
    )])

    await update.message.reply_html(
        "🍽 <b>Premium Menyu</b>\n\nKategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def branches_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    branches = await _get_branches()
    if not branches:
        await update.message.reply_html("📍 Hozircha filiallar kiritilmagan.")
        return

    text = "📍 <b>Bizning filiallar</b>\n\n"
    keyboard = []
    for b in branches:
        text += f"🏪 <b>{b.name}</b>\n"
        text += f"📌 {b.location_name}\n"
        if b.manager:
            text += f"👨‍💼 Menejer: {b.manager.name}\n"
        text += "\n"
        if b.location and isinstance(b.location, dict):
            lat = b.location.get('lat')
            lon = b.location.get('lon') or b.location.get('lng')
            if lat and lon:
                lat_str = f"{lat:.7f}"
                lon_str = f"{lon:.7f}"
                keyboard.append([InlineKeyboardButton(
                    f"🗺 {b.name} — Xaritada",
                    url=f"https://maps.google.com/?q={lat_str},{lon_str}"
                )])

    await update.message.reply_html(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )


async def aksiyalar_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    aksiyalar = await _get_active_aksiyalar()
    if not aksiyalar:
        await update.message.reply_html(
            "🎁 Hozircha aktiv aksiya yo'q.\nKuning davomida tekshirib turing!"
        )
        return

    text = "🎁 <b>Faol aksiyalar</b>\n\n"
    for a in aksiyalar:
        discounted = int(a.meal.price * (1 - a.discount / 100))
        text += (
            f"🔥 <b>{a.meal.name}</b>\n"
            f"💰 <del>{a.meal.price:,} UZS</del> → <b>{discounted:,} UZS</b>\n"
            f"   (-{a.discount}% chegirma!)\n"
            f"📅 {a.end_date.strftime('%d.%m.%Y')} gacha\n\n"
        )

    await update.message.reply_html(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🛒 Hozir buyurtma berish!",
                web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/")
            )
        ]])
    )


async def order_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    webapp_url = f"{SITE_URL}/tg-app/"
    await update.message.reply_html(
        "📲 <b>Buyurtma berish</b>\n\n"
        "Web App orqali tez va qulay buyurtma bering:\n\n"
        "✅ Menyudan taomlar tanlang\n"
        "✅ Savatga qo'shing\n"
        "✅ Ma'lumotlarni kiriting\n"
        "✅ To'lov usulini tanlang\n"
        "✅ Buyurtmani tasdiqlang\n\n"
        "🌐 Yoki saytimiz orqali: /sayt",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🍣 Web App ni ochish",
                web_app=WebAppInfo(url=webapp_url)
            )
        ], [
            InlineKeyboardButton(
                "🌐 Saytda buyurtma",
                url=f"{SITE_URL}/cart/"
            )
        ]])
    )


async def contact_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "📞 <b>Aloqa</b>\n\n"
        "📱 Telefon: <a href='tel:+998901234567'>+998 90 123 45 67</a>\n"
        "📸 Instagram: @umami_sushi_uz\n"
        "🌐 Sayt: <a href='{0}'>{0}</a>\n\n"
        "🕐 Ish vaqti:\n"
        "Dushanba — Yakshanba: 10:00 — 23:00\n\n"
        "💬 Savollar bo'lsa, shu chatga yozing!".format(SITE_URL)
    )


async def about_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "🍣 <b>UMAMI Premium Sushi Bot</b>\n\n"
        "Bu bot orqali:\n"
        "• 🍽 Menyuni ko'rish\n"
        "• 🎁 Aksiyalarni kuzatish\n"
        "• 📍 Filiallarni topish\n"
        "• 📲 Onlayn buyurtma berish\n\n"
        "mumkin!"
    )


async def sayt_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        f"🌐 <b>Onlayn buyurtma sayti:</b>\n\n"
        f"<a href='{SITE_URL}/menyu/'>🍣 Menyuni ko'rish</a>\n"
        f"<a href='{SITE_URL}/cart/'>🛒 Savat</a>\n"
        f"<a href='{SITE_URL}/aksiyalar/'>🎁 Aksiyalar</a>",
        disable_web_page_preview=True
    )


async def chat_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "💬 <b>Kassir bilan chat</b>\n\n"
        "Savolingizni yozing, kassir javob beradi.\n\n"
        "Mini App orqali chatdan foydalaning:\n"
        "👇 \"Buyurtma berish\" tugmasini bosing.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🛒 Mini Appni ochish", web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/"))
        ]])
    )


# ── Callback ─────────────────────────────────────────────────────
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('cat_'):
        cat_id = int(data.split('_')[1])
        try:
            category = await _get_category(cat_id)
            meals = await _get_meals_for_category(cat_id)
            if not meals:
                await query.edit_message_text("Bu kategoriyada taom yo'q.")
                return

            keyboard = []
            for meal in meals:
                price = meal.total_price()
                disc = f" 🔥-{meal.discount}%" if meal.discount > 0 else ""
                keyboard.append([InlineKeyboardButton(
                    f"🍣 {meal.name} — {price:,} UZS{disc}",
                    callback_data=f"meal_{meal.id}"
                )])
            keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="back_cats")])

            await query.edit_message_text(
                f"🍽 <b>{category.name}</b>\n\nTaomni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        except Category.DoesNotExist:
            await query.edit_message_text("Kategoriya topilmadi.")

    elif data.startswith('meal_'):
        meal_id = int(data.split('_')[1])
        try:
            meal = await _get_meal(meal_id)
            price = meal.total_price()

            text = f"🍣 <b>{meal.name}</b>\n\n"
            if meal.discount > 0:
                text += f"💰 <del>{meal.price:,} UZS</del> → <b>{price:,} UZS</b> (-{meal.discount}%)\n\n"
            else:
                text += f"💰 Narxi: <b>{price:,} UZS</b>\n\n"
            text += f"📝 {meal.description}"

            keyboard = [[
                InlineKeyboardButton("🛒 Buyurtma berish", web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/"))
            ], [
                InlineKeyboardButton("◀️ Orqaga", callback_data=f"cat_{meal.ctg.id}")
            ]]

            img = meal.get_first_image()
            try:
                if img:
                    full_url = f"{SITE_URL}{img}" if not img.startswith('http') else img
                    await query.message.reply_photo(
                        photo=full_url,
                        caption=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.delete_message()
                else:
                    raise Exception("no image")
            except Exception:
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )

        except Meal.DoesNotExist:
            await query.edit_message_text("Taom topilmadi.")

    elif data == 'back_cats':
        categories = await _get_active_categories()
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(f"🍽 {cat.name}", callback_data=f"cat_{cat.id}")])
        keyboard.append([InlineKeyboardButton(
            "🛒 Web App orqali buyurtma",
            web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/")
        )])
        await query.edit_message_text(
            "🍽 <b>Premium Menyu</b>\n\nKategoriyani tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )


# ── Unknown handler ──────────────────────────────────────────────
async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "😕 Tushunmadim. Iltimos, tugmalardan foydalaning yoki /start bosing.",
        reply_markup=main_keyboard()
    )


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update caused error: {ctx.error}", exc_info=ctx.error)


# ── Main ──────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sayt", sayt_handler))

    app.add_handler(MessageHandler(filters.Regex("^🍣 Menyu$"), menu_handler))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Aksiyalar$"), aksiyalar_handler))
    app.add_handler(MessageHandler(filters.Regex("^📍 Filiallar$"), branches_handler))
    app.add_handler(MessageHandler(filters.Regex("^📲 Buyurtma berish$"), order_handler))
    app.add_handler(MessageHandler(filters.Regex("^📞 Aloqa$"), contact_handler))
    app.add_handler(MessageHandler(filters.Regex("^💬 Kassir bilan chat$"), chat_handler))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Bot haqida$"), about_handler))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    app.add_error_handler(error_handler)

    logger.info(f"🤖 Foydalanuvchi Bot ishga tushdi!")
    logger.info(f"🌐 Sayt: {SITE_URL}")

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
