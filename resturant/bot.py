#!/usr/bin/env python
"""
UMAMI Premium Sushi — Telegram Bot
Bot: @amina_suhsi_order_bot
Admin: 6830116501
"""
import os
import sys
import django
import logging
import asyncio
import pytz
import requests

# Django sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
django.setup()

from django.conf import settings as dj_settings
from asgiref.sync import sync_to_async

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

from core.models import Meal, Category, Branch, Aksiya, Order, OrderItem, TelegramUser, Set

logging.basicConfig(
    format='%(asctime)s — %(levelname)s — %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = dj_settings.USER_BOT_TOKEN
ADMIN_ID = dj_settings.ADMIN_CHAT_ID
SITE_URL = dj_settings.SITE_URL

# ── Klaviaturalar ─────────────────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🍣 Menyu"), KeyboardButton("🎁 Aksiyalar")],
        [KeyboardButton("📍 Filiallar"), KeyboardButton("📦 Buyurtmalarim")],
        [KeyboardButton("📲 Buyurtma berish"), KeyboardButton("📞 Aloqa")],
        [KeyboardButton("ℹ️ Bot haqida")],
    ], resize_keyboard=True)


def webapp_keyboard():
    """Web App tugmasi"""
    webapp_url = f"{SITE_URL}/tg-app/"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🛒 Onlayn Buyurtma — Web App",
            web_app=WebAppInfo(url=webapp_url)
        )
    ], [
        InlineKeyboardButton("📱 Saytga o'tish", url=f"{SITE_URL}/menyu/")
    ]])


# ── Helpers (sync_to_async) ─────────────────────────────────────
@sync_to_async
def _get_or_create_tg_user(tg_id, username, first_name):
    return TelegramUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={'username': username, 'first_name': first_name}
    )

@sync_to_async
def _get_active_categories():
    return list(Category.objects.filter(is_active=True))

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

@sync_to_async
def _get_active_sets():
    return list(Set.objects.filter(is_active=True)[:10])

@sync_to_async
def _get_recent_orders():
    return list(Order.objects.filter(status__in=['new', 'confirmed']).order_by('-created_at')[:10])

@sync_to_async
def _get_order_stats():
    from datetime import date
    total = Order.objects.count()
    today_count = Order.objects.filter(created_at__date=date.today()).count()
    users = TelegramUser.objects.count()
    revenue = sum(o.total_amount for o in Order.objects.filter(status='done'))
    return total, today_count, users, revenue

@sync_to_async
def _update_order_status(order_id, status):
    Order.objects.filter(id=order_id).update(status=status)

@sync_to_async
def _get_order_items(order_id):
    try:
        order = Order.objects.get(id=order_id)
        return list(order.items.all())
    except Order.DoesNotExist:
        return []

@sync_to_async
def _get_orders_by_period(period):
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    now = timezone.now().astimezone(pytz.timezone('Asia/Tashkent'))
    
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        orders = Order.objects.filter(status='confirmed', created_at__gte=start).order_by('-created_at')
    elif period == 'yesterday':
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        orders = Order.objects.filter(status='confirmed', created_at__gte=start, created_at__lte=end).order_by('-created_at')
    elif period == 'week':
        week_ago = now - timedelta(days=7)
        orders = Order.objects.filter(status='confirmed', created_at__gte=week_ago).order_by('-created_at')
    elif period == '1month':
        from datetime import date
        month_ago = now - timedelta(days=30)
        orders = Order.objects.filter(status='confirmed', created_at__gte=month_ago).order_by('-created_at')
    elif period == '3months':
        month_ago = now - timedelta(days=90)
        orders = Order.objects.filter(status='confirmed', created_at__gte=month_ago).order_by('-created_at')
    elif period == '1year':
        month_ago = now - timedelta(days=365)
        orders = Order.objects.filter(status='confirmed', created_at__gte=month_ago).order_by('-created_at')
    else:
        orders = Order.objects.filter(status='confirmed').order_by('-created_at')[:50]
    
    return list(orders[:100])


# ── Handlers ─────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    tg_user, created = await _get_or_create_tg_user(
        user.id, user.username, user.first_name
    )

    text = (
        f"🍣 <b>UMAMI Premium Sushi</b> ga xush kelibsiz!\n\n"
        f"Salom, <b>{user.first_name}</b>! 👋\n\n"
        f"Biz Toshkentning eng yaxshi premium sushi restoranimiz.\n"
        f"Har bir taom — xususiy san'at asari.\n\n"
        f"⬇️ Quyidagi bo'limlardan birini tanlang:"
    )

    await update.message.reply_html(text, reply_markup=main_keyboard())

    if created:
        logger.info(f"Yangi foydalanuvchi: {user.id} — {user.first_name}")


async def menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    categories = await _get_active_categories()
    sets = await _get_active_sets()
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
    
    if sets:
        keyboard.append([InlineKeyboardButton("🎁 Maxsus Setlar", callback_data="show_sets")])
    
    keyboard.append([InlineKeyboardButton("🛒 Web App orqali buyurtma", web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/"))])

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
                keyboard.append([InlineKeyboardButton(
                    f"🗺 {b.name} — Xaritada ko'rish",
                    url=f"https://maps.google.com/?q={lat},{lon}"
                )])

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)


async def aksiyalar_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    aksiyalar = await _get_active_aksiyalar()
    if not aksiyalar:
        await update.message.reply_html("🎁 Hozircha aktiv aksiya mavjud emas.\nKuning davomida tekshirib turing!")
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
            InlineKeyboardButton("🛒 Hozir buyurtma berish!", web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/"))
        ]])
    )


async def order_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    webapp_url = f"{SITE_URL}/tg-app/"
    await update.message.reply_html(
        "📲 <b>Buyurtma berish</b>\n\n"
        "Quyidagi tugma orqali premium Web App ni oching:\n\n"
        "✅ Menyudan taomlar tanlang\n"
        "✅ Savatga qo'shing\n"
        "✅ Ma'lumotlarni kiriting\n"
        "✅ To'lov usulini tanlang\n"
        "✅ Buyurtmani tasdiqlang\n\n"
        "Buyurtma darhol adminга yuboriladi! 🚀",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🍣 Web App ni ochish",
                web_app=WebAppInfo(url=webapp_url)
            )
        ], [
            InlineKeyboardButton("🌐 Saytda buyurtma", url=f"{SITE_URL}/cart/")
        ]])
    )


async def contact_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "📞 <b>Aloqa</b>\n\n"
        "📱 Telefon: <a href='tel:+998901234567'>+998 90 123 45 67</a>\n"
        "📸 Instagram: @umami_sushi_uz\n"
        "🌐 Sayt: umami.uz\n\n"
        "🕐 Ish vaqti:\n"
        "Dushanba — Yakshanba: 10:00 — 23:00\n\n"
        "💬 Savollar va takliflar uchun yozing!"
    )


async def orders_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Bugun", callback_data="orders_today")],
        [InlineKeyboardButton("📅 Kecha", callback_data="orders_yesterday")],
        [InlineKeyboardButton("📅 Shu hafta", callback_data="orders_week")],
        [InlineKeyboardButton("📅 1 oy", callback_data="orders_1month")],
        [InlineKeyboardButton("📅 3 oy", callback_data="orders_3months")],
        [InlineKeyboardButton("📅 1 yil", callback_data="orders_1year")],
    ]
    await update.message.reply_html(
        "📦 <b>Buyurtmalarim</b>\n\nVaqt oralig'ini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def orders_callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    period = data.replace('orders_', '')
    period_names = {
        'today': '📅 Bugun',
        'yesterday': '📅 Kecha',
        'week': '📅 Shu hafta',
        '1month': '📅 1 oy',
        '3months': '📅 3 oy',
        '1year': '📅 1 yil'
    }
    
    orders = await _get_orders_by_period(period)
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    
    if not orders:
        await query.edit_message_text(
            f"📦 <b>Buyurtmalarim</b>\n\n{period_names.get(period, '')}\n\n❌ Bu davrda buyurtmalar topilmadi.",
            parse_mode=ParseMode.HTML
        )
        return
    
    total_amount = sum(o.total_amount for o in orders)
    count = len(orders)
    
    cols = 2
    
    text = f"📦 <b>Buyurtmalarim</b>\n\n{period_names.get(period, '')}\n\n"
    text += f"📊 Jami: {count} ta buyurtma | 💰 {total_amount:,} UZS\n\n"
    
    keyboard = []
    row = []
    
    for i, order in enumerate(orders):
        order_time = order.created_at.astimezone(tashkent_tz)
        date_str = order_time.strftime('%d.%m')
        time_str = order_time.strftime('%H:%M')
        
        status_icon = {
            'new': '🆕',
            'confirmed': '✅',
            'done': '🎉',
            'cancelled': '❌'
        }.get(order.status, '❓')
        
        btn_text = f"{status_icon} #{order.id} - {date_str} {time_str}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"order_detail_{order.id}"))
        
        if len(row) >= cols:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="back_orders")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )


async def order_detail_callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'back_orders':
        keyboard = [
            [InlineKeyboardButton("📅 Bugun", callback_data="orders_today")],
            [InlineKeyboardButton("📅 Kecha", callback_data="orders_yesterday")],
            [InlineKeyboardButton("📅 Shu hafta", callback_data="orders_week")],
            [InlineKeyboardButton("📅 1 oy", callback_data="orders_1month")],
            [InlineKeyboardButton("📅 3 oy", callback_data="orders_3months")],
            [InlineKeyboardButton("📅 1 yil", callback_data="orders_1year")],
        ]
        await query.edit_message_text(
            "📦 <b>Buyurtmalarim</b>\n\nVaqt oralig'ini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    if data.startswith('order_detail_'):
        order_id = int(data.replace('order_detail_', ''))
        try:
            order = Order.objects.get(id=order_id)
            items = order.items.all()
            tashkent_tz = pytz.timezone('Asia/Tashkent')
            order_time = order.created_at.astimezone(tashkent_tz)
            
            items_text = '\n'.join([
                f"  • {item.meal_name} x{item.quantity} — {item.price:,} UZS"
                for item in items
            ])
            
            status_text = {
                'new': '🆕 Yangi',
                'confirmed': '✅ Tasdiqlangan',
                'done': '🎉 Tugatilgan',
                'cancelled': '❌ Bekor qilingan'
            }.get(order.status, order.status)
            
            text = (
                f"📦 <b>Buyurtma #{order.id}</b>\n\n"
                f"📌 Holat: {status_text}\n"
                f"👤 {order.full_name}\n"
                f"📞 {order.phone}\n"
                f"📍 {order.address}\n\n"
                f"🛒 <b>Buyurtma:</b>\n{items_text}\n\n"
                f"💰 <b>Jami: {order.total_amount:,} UZS</b>\n"
                f"💳 To'lov: {order.get_payment_method_display()}\n"
                f"🕐 {order_time.strftime('%d.%m.%Y %H:%M')} (Toshkent)"
            )
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Orqaga", callback_data="back_orders")
                ]])
            )
        except Order.DoesNotExist:
            await query.answer("Buyurtma topilmadi!", show_alert=True)


async def about_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "🍣 <b>UMAMI Premium Sushi Bot</b>\n\n"
        "Bu bot orqali siz:\n"
        "• 🍽 Menyuni ko'rishingiz\n"
        "• 🎁 Aksiyalar haqida bilib olishingiz\n"
        "• 📍 Filiallarni topishingiz\n"
        "• 📲 Onlayn buyurtma berishingiz mumkin\n\n"
        "🔧 Muammo yuz bersa, /start bosing."
    )


# ── Callback: menyu kategoriya ─────────────────────────────────
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
            keyboard.append([InlineKeyboardButton("◀️ Kategoriyalar", callback_data="back_cats")])

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
        sets = await _get_active_sets()
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(f"🍽 {cat.name}", callback_data=f"cat_{cat.id}")])
        if sets:
            keyboard.append([InlineKeyboardButton("🎁 Maxsus Setlar", callback_data="show_sets")])
        keyboard.append([InlineKeyboardButton("🛒 Web App orqali buyurtma", web_app=WebAppInfo(url=f"{SITE_URL}/tg-app/"))])
        await query.edit_message_text(
            "🍽 <b>Premium Menyu</b>\n\nKategoriyani tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    elif data == 'show_sets':
        sets = await _get_active_sets()
        if not sets:
            await query.edit_message_text("🎁 Hozircha setlar yo'q.")
            return
        text = "🎁 <b>Maxsus Setlar</b>\n\n"
        keyboard = []
        for s in sets:
            old_price = f" <del>{s.old_price:,}</del>" if s.old_price else ""
            text += f"• <b>{s.name}</b>{old_price} — {s.price:,} UZS\n"
            text += f"  📝 {s.description[:60]}...\n\n"
        keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="back_cats")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data.startswith('confirm_'):
        order_id = int(data.split('_')[1])
        await _update_order_status(order_id, 'confirmed')
        await query.answer("✅ Buyurtma tasdiqlandi!", show_alert=True)
        try:
            txt = query.message.text or query.message.caption or ""
            await query.edit_message_text(
                txt + "\n\n✅ <b>TASDIQLANDI</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

    elif data.startswith('cancel_'):
        order_id = int(data.split('_')[1])
        await _update_order_status(order_id, 'cancelled')
        await query.answer("❌ Buyurtma bekor qilindi", show_alert=True)
        try:
            txt = query.message.text or query.message.caption or ""
            await query.edit_message_text(
                txt + "\n\n❌ <b>BEKOR QILINDI</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass


# ── Admin komandalar ────────────────────────────────────────────
async def admin_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return

    orders = await _get_recent_orders()
    if not orders:
        await update.message.reply_text("📦 Yangi buyurtmalar yo'q.")
        return

    for order in orders:
        items = await _get_order_items(order.id)
        items_text = '\n'.join([f"  • {i.meal_name} x{i.quantity} — {i.price:,} UZS" for i in items])
        order_time = order.created_at.astimezone(pytz.timezone('Asia/Tashkent'))
        txt = (
            f"📦 <b>Buyurtma #{order.id}</b> [{order.get_status_display()}]\n"
            f"👤 {order.full_name}\n📞 {order.phone}\n📍 {order.address}\n\n"
            f"{items_text}\n\n"
            f"💰 <b>Jami: {order.total_amount:,} UZS</b>\n"
            f"💳 {order.get_payment_method_display()}\n"
            f"🕐 {order_time.strftime('%d.%m.%Y %H:%M')} (Toshkent)"
        )
        kb = [[
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{order.id}"),
            InlineKeyboardButton("❌ Bekor", callback_data=f"cancel_{order.id}"),
        ]]
        await update.message.reply_html(txt, reply_markup=InlineKeyboardMarkup(kb))


async def admin_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total, today_count, users, revenue = await _get_order_stats()
    await update.message.reply_html(
        f"📊 <b>Statistika</b>\n\n"
        f"📦 Jami buyurtmalar: <b>{total}</b>\n"
        f"📅 Bugungi: <b>{today_count}</b>\n"
        f"👥 Bot foydalanuvchilari: <b>{users}</b>\n"
        f"💰 Jami daromad: <b>{revenue:,} UZS</b>"
    )


async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "😕 Tushunmadim. Iltimos, quyidagi tugmalardan foydalaning.",
        reply_markup=main_keyboard()
    )


async def error_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {ctx.error}", exc_info=ctx.error)


# ── Main ──────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    # Webhook sozlash
    webhook_url = f"{SITE_URL}/webhook/"
    try:
        resp = requests.post(
            f'https://api.telegram.org/bot{TOKEN}/setWebhook',
            json={'url': webhook_url},
            timeout=10
        )
        if resp.json().get('ok'):
            print(f"✅ Webhook o'rnatildi: {webhook_url}")
        else:
            print(f"⚠️ Webhook xatosi: {resp.json()}")
    except Exception as e:
        print(f"⚠️ Webhook sozlab bo'lmadi: {e}")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CommandHandler("stats", admin_stats))

    app.add_handler(MessageHandler(filters.Regex("^🍣 Menyu$"), menu_handler))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Aksiyalar$"), aksiyalar_handler))
    app.add_handler(MessageHandler(filters.Regex("^📍 Filiallar$"), branches_handler))
    app.add_handler(MessageHandler(filters.Regex("^📦 Buyurtmalarim$"), orders_handler))
    app.add_handler(MessageHandler(filters.Regex("^📲 Buyurtma berish$"), order_handler))
    app.add_handler(MessageHandler(filters.Regex("^📞 Aloqa$"), contact_handler))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Bot haqida$"), about_handler))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(orders_callback_handler, pattern='^orders_'))
    app.add_handler(CallbackQueryHandler(order_detail_callback_handler, pattern='^(order_detail_|back_orders)$'))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    app.add_error_handler(error_handler)

    logger.info(f"🤖 Bot ishga tushdi! Token: {TOKEN[:20]}...")
    logger.info(f"👑 Admin ID: {ADMIN_ID}")
    logger.info(f"🌐 Sayt: {SITE_URL}")

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
