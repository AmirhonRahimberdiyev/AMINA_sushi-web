#!/usr/bin/env python
"""
UMAMI Premium Sushi — Staff Bot (Admin/Xodimlar uchun)
Bot: @umami_staff_bot
Admin Chat ID: 6830116501
"""
import os
import django
import pytz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
django.setup()

from django.conf import settings as dj_settings
from asgiref.sync import sync_to_async
from datetime import date, timedelta
import logging

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from core.models import Meal, Category, Branch, Aksiya, Order, OrderItem, TelegramUser, MealImage

logging.basicConfig(
    format='%(asctime)s — [STAFF BOT] — %(levelname)s — %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = dj_settings.STAFF_BOT_TOKEN
ADMIN_ID = dj_settings.ADMIN_CHAT_ID
SITE_URL = dj_settings.SITE_URL

# ── Conversation states ─────────────────────────────────────────
ADD_MEAL_NAME, ADD_MEAL_DESC, ADD_MEAL_PRICE, ADD_MEAL_CAT, ADD_MEAL_DISCOUNT, ADD_MEAL_PHOTO = range(6)
ADD_CATEGORY_NAME = range(7)
ADD_AKSIYA_MEAL, ADD_AKSIYA_DISCOUNT, ADD_AKSIYA_DAYS = range(8, 11)

temp_data = {}

# ── Helpers ─────────────────────────────────────────────────────
def is_admin(user_id):
    return user_id == ADMIN_ID

@sync_to_async
def _get_orders_by_date_range(start_date, end_date):
    from datetime import datetime
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    qs = Order.objects.filter(
        created_at__gte=start_dt,
        created_at__lte=end_dt
    ).order_by('-created_at')[:30]
    orders = list(qs)
    total_count = Order.objects.filter(
        created_at__gte=start_dt,
        created_at__lte=end_dt
    ).count()
    total_revenue = sum(o.total_amount for o in orders if o.status not in ['cancelled'])
    return orders, total_count, total_revenue

@sync_to_async
def _get_orders(status=None, days=1):
    qs = Order.objects.all()
    if status:
        qs = qs.filter(status=status)
    else:
        qs = qs.filter(created_at__gte=date.today() - timedelta(days=days))
    return list(qs.order_by('-created_at')[:15])

@sync_to_async
def _get_order_detail(order_id):
    try:
        order = Order.objects.get(id=order_id)
        items = list(order.items.all())
        return order, items
    except Order.DoesNotExist:
        return None, []

@sync_to_async
def _update_order_status(order_id, status):
    Order.objects.filter(id=order_id).update(status=status)

@sync_to_async
def _get_order_items(order_id):
    try:
        return list(Order.objects.get(id=order_id).items.all())
    except Order.DoesNotExist:
        return []

@sync_to_async
def _get_stats():
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    yesterday_orders = Order.objects.filter(created_at__date=yesterday).count()
    week_orders = Order.objects.filter(created_at__gte=week_ago).count()

    today_revenue = sum(o.total_amount for o in Order.objects.filter(created_at__date=today, status__in=['confirmed', 'cooking', 'delivering', 'done']))
    week_revenue = sum(o.total_amount for o in Order.objects.filter(created_at__gte=week_ago, status__in=['confirmed', 'cooking', 'delivering', 'done']))
    total_revenue = sum(o.total_amount for o in Order.objects.filter(status__in=['confirmed', 'cooking', 'delivering', 'done']))

    new_orders = Order.objects.filter(status='new').count()
    cooking = Order.objects.filter(status='cooking').count()
    delivering = Order.objects.filter(status='delivering').count()
    done = Order.objects.filter(status='done').count()
    cancelled = Order.objects.filter(status='cancelled').count()

    users_count = TelegramUser.objects.count()
    meals_count = Meal.objects.count()
    categories_count = Category.objects.filter(is_active=True).count()

    return {
        'total_orders': total_orders,
        'today_orders': today_orders,
        'yesterday_orders': yesterday_orders,
        'week_orders': week_orders,
        'today_revenue': today_revenue,
        'week_revenue': week_revenue,
        'total_revenue': total_revenue,
        'new_orders': new_orders,
        'cooking': cooking,
        'delivering': delivering,
        'done': done,
        'cancelled': cancelled,
        'users_count': users_count,
        'meals_count': meals_count,
        'categories_count': categories_count,
    }

@sync_to_async
def _get_categories():
    return list(Category.objects.all().order_by('id'))

@sync_to_async
def _get_meals_by_category(cat_id):
    return list(Meal.objects.filter(ctg_id=cat_id).order_by('id'))

@sync_to_async
def _get_all_meals():
    return list(Meal.objects.select_related('ctg').order_by('-id')[:20])

@sync_to_async
def _delete_meal(meal_id):
    Meal.objects.filter(id=meal_id).delete()

@sync_to_async
def _update_meal_price(meal_id, price):
    Meal.objects.filter(id=meal_id).update(price=price)

@sync_to_async
def _update_meal_discount(meal_id, discount):
    Meal.objects.filter(id=meal_id).update(discount=discount)

@sync_to_async
def _create_meal(name, description, price, ctg_id, discount=0):
    return Meal.objects.create(
        name=name, description=description, price=price,
        ctg_id=ctg_id, discount=discount
    )

@sync_to_async
def _create_category(name):
    return Category.objects.create(name=name, is_active=True)

@sync_to_async
def _create_aksiya(meal_id, discount, days):
    from datetime import date, timedelta
    meal = Meal.objects.get(id=meal_id)
    end = date.today() + timedelta(days=days)
    return Aksiya.objects.create(
        meal=meal, discount=discount,
        start_date=date.today(), end_date=end, is_active=True
    )

@sync_to_async
def _get_active_aksiyalar():
    return list(Aksiya.objects.filter(is_active=True).select_related('meal').order_by('-id'))

@sync_to_async
def _toggle_aksiya(aksiya_id):
    a = Aksiya.objects.get(id=aksiya_id)
    a.is_active = not a.is_active
    a.save()
    return a.is_active

@sync_to_async
def _toggle_category(cat_id):
    cat = Category.objects.get(id=cat_id)
    cat.is_active = not cat.is_active
    cat.save()
    return cat.is_active

@sync_to_async
def _get_top_meals(days=7):
    from datetime import date, timedelta
    since = date.today() - timedelta(days=days)
    from django.db.models import Sum, Count
    top = OrderItem.objects.filter(
        order__created_at__gte=since
    ).values('meal_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_qty')[:5]
    return list(top)


# ── Klaviaturalar ─────────────────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📦 Buyurtmalar"), KeyboardButton("📊 Statistika")],
        [KeyboardButton("🍽 Menyu boshqarish"), KeyboardButton("🎁 Aksiyalar")],
        [KeyboardButton("👥 Foydalanuvchilar")],
    ], resize_keyboard=True)


# ── Start ─────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return

    await update.message.reply_html(
        "👨‍💼 <b>UMAMI Staff Panel</b>\n\n"
        f"Salom, <b>{update.effective_user.first_name}</b>!\n\n"
        "🛠 Bu admin panel orqali:\n"
        "• 📦 Buyurtmalarni boshqarish\n"
        "• 📊 Statistika ko'rish\n"
        "• 🍽 Menyuni tahrirlash\n"
        "• 🎁 Aksiyalar yaratish\n"
        "• 👥 Foydalanuvchilarni ko'rish\n\n"
        "mumkin!",
        reply_markup=main_keyboard()
    )


# ── Buyurtmalar ───────────────────────────────────────────────────
async def orders_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    kb = [
        [
            InlineKeyboardButton("📅 Bugun", callback_data="orders_today"),
            InlineKeyboardButton("📅 Kecha", callback_data="orders_yesterday"),
        ],
        [
            InlineKeyboardButton("📅 Bu hafta", callback_data="orders_week"),
            InlineKeyboardButton("📅 Bu oy", callback_data="orders_month"),
        ],
        [
            InlineKeyboardButton("🆕 Yangi", callback_data="orders_status_new"),
            InlineKeyboardButton("📦 Hammasi", callback_data="orders_status_all"),
        ],
    ]

    text = (
        "📦 <b>Buyurtmalar</b>\n\n"
        "Qaysi davrni ko'rmoqchisiz?"
    )

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(kb))


async def orders_date_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    query = update.callback_query
    await query.answer()
    data = query.data

    today = date.today()

    if data == 'orders_today':
        start = today
        end = today
        label = "Bugun"
    elif data == 'orders_yesterday':
        start = today - timedelta(days=1)
        end = today - timedelta(days=1)
        label = "Kecha"
    elif data == 'orders_week':
        start = today - timedelta(days=7)
        end = today
        label = "Bu hafta (7 kun)"
    elif data == 'orders_month':
        start = today - timedelta(days=30)
        end = today
        label = "Bu oy (30 kun)"
    else:
        return

    orders, total_count, total_revenue = await _get_orders_by_date_range(start, end)

    if not orders:
        await query.edit_message_text(f"📦 <b>{label}</b> — buyurtmalar yo'q.", parse_mode=ParseMode.HTML)
        return

    header = f"📦 <b>{label}</b>\n\n📋 Buyurtmalar: <b>{total_count}</b> ta\n💰 Daromad: <b>{total_revenue:,} UZS</b>\n\n"

    kb = []
    for order in orders:
        status_emoji = {
            'new': '🆕', 'confirmed': '✅', 'cooking': '🔥',
            'delivering': '🚗', 'done': '🏁', 'cancelled': '❌'
        }
        emoji = status_emoji.get(order.status, '📦')
        tashkent_tz = pytz.timezone('Asia/Tashkent')
        order_time = order.created_at.astimezone(tashkent_tz)
        kb.append([InlineKeyboardButton(
            f"📄 #{order.id} {order.get_status_display()}",
            callback_data=f"order_detail_{order.id}"
        )])

    kb.append([InlineKeyboardButton("◀️ Orqaga", callback_data="orders_back")])

    await query.edit_message_text(header, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


async def orders_status_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'orders_status_all':
        status_filter = None
        label = "Barcha buyurtmalar"
        orders = await sync_to_async(lambda: list(Order.objects.order_by('-created_at')[:30]))()
        total_count = Order.objects.count()
    else:
        status_code = data.replace('orders_status_', '')
        status_filter = status_code
        label = dict(Order.STATUS_CHOICES).get(status_code, status_code)
        orders = await sync_to_async(lambda: list(Order.objects.filter(status=status_code).order_by('-created_at')[:30]))()
        total_count = Order.objects.filter(status=status_code).count()

    if not orders:
        await query.edit_message_text(f"📦 <b>{label}</b> — buyurtmalar yo'q.", parse_mode=ParseMode.HTML)
        return

    header = f"📦 <b>{label}</b>\n\n📋 Buyurtmalar: <b>{total_count}</b> ta\n\n"

    kb = []
    for order in orders:
        status_emoji = {
            'new': '🆕', 'confirmed': '✅', 'cooking': '🔥',
            'delivering': '🚗', 'done': '🏁', 'cancelled': '❌'
        }
        emoji = status_emoji.get(order.status, '📦')
        tashkent_tz = pytz.timezone('Asia/Tashkent')
        order_time = order.created_at.astimezone(tashkent_tz)
        kb.append([InlineKeyboardButton(
            f"📄 #{order.id} {order.get_status_display()}",
            callback_data=f"order_detail_{order.id}"
        )])

    kb.append([InlineKeyboardButton("◀️ Orqaga", callback_data="orders_back")])

    await query.edit_message_text(header, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


async def order_detail_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace('order_detail_', ''))

    order, items = await _get_order_detail(order_id)
    if not order:
        await query.edit_message_text("Buyurtma topilmadi.")
        return

    status_emoji = {
        'new': '🆕', 'confirmed': '✅', 'cooking': '🔥',
        'delivering': '🚗', 'done': '🏁', 'cancelled': '❌'
    }
    emoji = status_emoji.get(order.status, '📦')

    items_text = '\n'.join([f"  • {i.meal_name} x{i.quantity} — {i.price:,} UZS" for i in items])

    branch_info = ""
    if order.branch:
        branch_info = f"🏪 <b>Filial:</b> {order.branch.name}\n"

    # Tashkent vaqti
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    order_time = order.created_at.astimezone(tashkent_tz)

    txt = (
        f"{emoji} <b>Buyurtma #{order.id}</b>\n\n"
        f"👤 {order.full_name}\n📞 {order.phone}\n📍 {order.address}\n"
        f"{branch_info}\n"
        f"🛒 <b>Tarkibi:</b>\n{items_text}\n\n"
        f"💰 <b>Jami: {order.total_amount:,} UZS</b>\n"
        f"💳 {order.get_payment_method_display()}\n"
        f"📌 {order.get_source_display()}\n"
        f"📊 {order.get_status_display()}\n"
        f"🕐 {order_time.strftime('%d.%m.%Y %H:%M')} (Toshkent)"
    )

    kb = []
    if order.status == 'new':
        kb.append([
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"staff_confirm_{order.id}"),
            InlineKeyboardButton("❌ Bekor", callback_data=f"staff_cancel_{order.id}"),
        ])
    elif order.status == 'confirmed':
        kb.append([InlineKeyboardButton("🔥 Tayyorlanmoqda", callback_data=f"staff_cooking_{order.id}")])
    elif order.status == 'cooking':
        kb.append([InlineKeyboardButton("🚗 Yetkazilmoqda", callback_data=f"staff_delivering_{order.id}")])
    elif order.status == 'delivering':
        kb.append([InlineKeyboardButton("🏁 Bajarildi", callback_data=f"staff_done_{order.id}")])

    kb.append([InlineKeyboardButton("◀️ Orqaga", callback_data="orders_back")])

    await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb) if kb else None, parse_mode=ParseMode.HTML)


# ── Statistika ────────────────────────────────────────────────────
async def stats_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    s = await _get_stats()

    txt = (
        f"📊 <b>UMAMI Statistika</b>\n\n"
        f"📦 <b>Buyurtmalar:</b>\n"
        f"  🆕 Yangi: {s['new_orders']}\n"
        f"  🔥 Tayyorlanmoqda: {s['cooking']}\n"
        f"  🚗 Yetkazilmoqda: {s['delivering']}\n"
        f"  ✅ Bajarildi: {s['done']}\n"
        f"  ❌ Bekor: {s['cancelled']}\n\n"
        f"📅 <b>Davriy:</b>\n"
        f"  Bugun: {s['today_orders']} ta\n"
        f"  Kecha: {s['yesterday_orders']} ta\n"
        f"  Hafta: {s['week_orders']} ta\n"
        f"  Jami: {s['total_orders']} ta\n\n"
        f"💰 <b>Daromad:</b>\n"
        f"  Bugun: {s['today_revenue']:,} UZS\n"
        f"  Hafta: {s['week_revenue']:,} UZS\n"
        f"  Jami: {s['total_revenue']:,} UZS\n\n"
        f"👥 Bot foydalanuvchilari: {s['users_count']}\n"
        f"🍽 Taomlar: {s['meals_count']}\n"
        f"📂 Kategoriyalar: {s['categories_count']}"
    )

    # Top meals
    top = await _get_top_meals()
    if top:
        txt += "\n\n🏆 <b>Top taomlar (7 kun):</b>\n"
        for i, t in enumerate(top, 1):
            txt += f"  {i}. {t['meal_name']} — {t['total_qty']} dona\n"

    await update.message.reply_html(txt)


# ── Menyu boshqarish ─────────────────────────────────────────────
async def menu_manage_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    categories = await _get_categories()
    keyboard = []
    for cat in categories:
        status = "✅" if cat.is_active else "❌"
        keyboard.append([InlineKeyboardButton(
            f"{status} {cat.name}",
            callback_data=f"menu_cat_{cat.id}"
        )])
    keyboard.append([InlineKeyboardButton("➕ Kategoriya qo'shish", callback_data="menu_add_cat")])
    keyboard.append([InlineKeyboardButton("➕ Taom qo'shish", callback_data="menu_add_meal")])
    keyboard.append([InlineKeyboardButton("📋 Barcha taomlar", callback_data="menu_all_meals")])

    await update.message.reply_html(
        "🍽 <b>Menyu Boshqarish</b>\n\nKategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ── Aksiyalar ─────────────────────────────────────────────────────
async def aksiyalar_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    aksiyalar = await _get_active_aksiyalar()
    if not aksiyalar:
        await update.message.reply_text("🎁 Faol aksiya yo'q.\n\n➕ Yangi aksiya qo'shish: /add_aksiya")
        return

    keyboard = []
    text = "🎁 <b>Faol aksiyalar</b>\n\n"
    for a in aksiyalar:
        discounted = int(a.meal.price * (1 - a.discount / 100))
        text += (
            f"🔥 {a.meal.name}\n"
            f"💰 <del>{a.meal.price:,}</del> → <b>{discounted:,} UZS</b>\n"
            f"📅 {a.end_date.strftime('%d.%m.%Y')} gacha\n\n"
        )
        keyboard.append([InlineKeyboardButton(
            f"❌ {a.meal.name} — o'chirish",
            callback_data=f"aksiya_off_{a.id}"
        )])
    keyboard.append([InlineKeyboardButton("➕ Yangi aksiya", callback_data="aksiya_add")])

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ── Foydalanuvchilar ─────────────────────────────────────────────
async def users_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    count = await sync_to_async(TelegramUser.objects.count)()
    recent = await sync_to_async(lambda: list(TelegramUser.objects.order_by('-created_at')[:10]))()

    txt = f"👥 <b>Foydalanuvchilar</b>\n\nJami: <b>{count}</b>\n\n"
    txt += "Oxirgi 10 ta:\n"
    for u in recent:
        name = u.first_name or 'Noma\'lum'
        uname = u.username or '-'
        txt += f"• {name} (@{uname}) — {u.tg_id}\n"

    await update.message.reply_html(txt)


# ── Callback handler ─────────────────────────────────────────────
async def staff_button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.callback_query.answer("❌ Ruxsat yo'q!")
        return

    query = update.callback_query
    await query.answer()
    data = query.data

    # Order list views
    if data == 'orders_today':
        await orders_date_handler(update, ctx)
    elif data == 'orders_yesterday':
        await orders_date_handler(update, ctx)
    elif data == 'orders_week':
        await orders_date_handler(update, ctx)
    elif data == 'orders_month':
        await orders_date_handler(update, ctx)
    elif data in ('orders_status_new', 'orders_status_all'):
        await orders_status_handler(update, ctx)
    elif data == 'orders_back':
        kb = [
            [
                InlineKeyboardButton("📅 Bugun", callback_data="orders_today"),
                InlineKeyboardButton("📅 Kecha", callback_data="orders_yesterday"),
            ],
            [
                InlineKeyboardButton("📅 Bu hafta", callback_data="orders_week"),
                InlineKeyboardButton("📅 Bu oy", callback_data="orders_month"),
            ],
            [
                InlineKeyboardButton("🆕 Yangi", callback_data="orders_status_new"),
                InlineKeyboardButton("📦 Hammasi", callback_data="orders_status_all"),
            ],
        ]
        await query.edit_message_text(
            "📦 <b>Buyurtmalar</b>\n\nQaysi davrni ko'rmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.HTML
        )
    elif data.startswith('order_detail_'):
        await order_detail_handler(update, ctx)

    # Order status updates — from notifications (confirm_123, cancel_123)
    if data.startswith('confirm_'):
        oid = int(data.split('_')[1])
        await _update_order_status(oid, 'confirmed')
        await query.answer("✅ Tasdiqlandi!", show_alert=True)
        try:
            txt = query.message.text or query.message.caption or ""
            await query.edit_message_text(txt + "\n\n✅ <b>TASDIQLANDI</b>", parse_mode=ParseMode.HTML)
        except:
            pass

    elif data.startswith('cancel_'):
        oid = int(data.split('_')[1])
        await _update_order_status(oid, 'cancelled')
        await query.answer("❌ Bekor qilindi!", show_alert=True)
        try:
            txt = query.message.text or query.message.caption or ""
            await query.edit_message_text(txt + "\n\n❌ <b>BEKOR QILINDI</b>", parse_mode=ParseMode.HTML)
        except:
            pass

    # Order status updates — from staff panel (staff_confirm_123, staff_cancel_123)
    elif data.startswith('staff_confirm_'):
        oid = int(data.split('_')[2])
        await _update_order_status(oid, 'confirmed')
        await query.answer("✅ Tasdiqlandi!", show_alert=True)
        try:
            txt = query.message.text or query.message.caption or ""
            await query.edit_message_text(txt.replace('🆕', '✅').replace('[Yangi]', '[Tasdiqlangan]'), parse_mode=ParseMode.HTML)
        except:
            pass

    elif data.startswith('staff_cancel_'):
        oid = int(data.split('_')[2])
        await _update_order_status(oid, 'cancelled')
        await query.answer("❌ Bekor qilindi!", show_alert=True)
        try:
            txt = query.message.text or query.message.caption or ""
            await query.edit_message_text(txt.replace('🆕', '❌').replace('[Yangi]', '[Bekor]'), parse_mode=ParseMode.HTML)
        except:
            pass

    elif data.startswith('staff_cooking_'):
        oid = int(data.split('_')[2])
        await _update_order_status(oid, 'cooking')
        await query.answer("🔥 Tayyorlanmoqda!", show_alert=True)
        await refresh_order_message(query, oid, 'cooking', '🔥', 'Tayyorlanmoqda')

    elif data.startswith('staff_delivering_'):
        oid = int(data.split('_')[2])
        await _update_order_status(oid, 'delivering')
        await query.answer("🚗 Yetkazilmoqda!", show_alert=True)
        await refresh_order_message(query, oid, 'delivering', '🚗', 'Yetkazilmoqda')

    elif data.startswith('staff_done_'):
        oid = int(data.split('_')[2])
        await _update_order_status(oid, 'done')
        await query.answer("🏁 Bajarildi!", show_alert=True)
        await refresh_order_message(query, oid, 'done', '🏁', 'Bajarildi')

    # Menu management
    elif data.startswith('menu_cat_'):
        cat_id = int(data.split('_')[2])
        meals = await _get_meals_by_category(cat_id)
        cat = await sync_to_async(lambda: Category.objects.get(id=cat_id))()

        text = f"📂 <b>{cat.name}</b>"
        status_str = "✅ Faol" if cat.is_active else "❌ O'chirilgan"
        text += f" ({status_str})\n\n"
        kb = []
        if meals:
            for m in meals:
                price = m.total_price()
                text += f"• {m.name} — {price:,} UZS\n"
                kb.append([
                    InlineKeyboardButton("💰 Narx", callback_data=f"price_{m.id}"),
                    InlineKeyboardButton("📝 %", callback_data=f"disc_{m.id}"),
                    InlineKeyboardButton("🗑", callback_data=f"del_{m.id}"),
                ])
        else:
            text += "Taom yo'q."
        kb.append([InlineKeyboardButton("➕ Taom qo'shish", callback_data=f"add_meal_to_{cat_id}")])
        kb.append([InlineKeyboardButton(
            "✅" if cat.is_active else "❌",
            callback_data=f"toggle_cat_{cat_id}"
        ), InlineKeyboardButton("◀️ Orqaga", callback_data="menu_back")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'menu_add_cat':
        await query.message.reply_text("📂 Yangi kategoriya nomini yuboring:")
        ctx.user_data['awaiting'] = 'cat_name'

    elif data == 'menu_add_meal':
        cats = await _get_categories()
        kb = [[InlineKeyboardButton(c.name, callback_data=f"add_meal_to_{c.id}")] for c in cats if c.is_active]
        kb.append([InlineKeyboardButton("◀️ Orqaga", callback_data="menu_back")])
        await query.edit_message_text("🍣 Qaysi kategoriaga taom qo'shasiz?", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith('add_meal_to_'):
        cat_id = int(data.split('_')[3])
        ctx.user_data['add_meal_cat'] = cat_id
        ctx.user_data['awaiting'] = 'meal_name'
        await query.message.reply_text("🍣 Taom nomini yuboring:")

    elif data == 'menu_all_meals':
        meals = await _get_all_meals()
        text = "📋 <b>Barcha taomlar</b>\n\n"
        kb = []
        for m in meals:
            price = m.total_price()
            text += f"• {m.name} ({m.ctg.name}) — {price:,} UZS\n"
            kb.append([
                InlineKeyboardButton("💰 Narx", callback_data=f"price_{m.id}"),
                InlineKeyboardButton("📝 %", callback_data=f"disc_{m.id}"),
                InlineKeyboardButton("🗑", callback_data=f"del_{m.id}"),
            ])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'menu_back':
        categories = await _get_categories()
        keyboard = []
        for cat in categories:
            status = "✅" if cat.is_active else "❌"
            keyboard.append([InlineKeyboardButton(f"{status} {cat.name}", callback_data=f"menu_cat_{cat.id}")])
        keyboard.append([InlineKeyboardButton("➕ Kategoriya qo'shish", callback_data="menu_add_cat")])
        keyboard.append([InlineKeyboardButton("➕ Taom qo'shish", callback_data="menu_add_meal")])
        keyboard.append([InlineKeyboardButton("📋 Barcha taomlar", callback_data="menu_all_meals")])
        await query.edit_message_text("🍽 <b>Menyu Boshqarish</b>\n\nKategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data.startswith('toggle_cat_'):
        cat_id = int(data.split('_')[2])
        active = await _toggle_category(cat_id)
        msg = "✅ Faol" if active else "❌ O'chirildi"
        await query.answer(msg, show_alert=True)
        await staff_button_handler(update, ctx)

    elif data.startswith('price_'):
        meal_id = int(data.split('_')[1])
        ctx.user_data['awaiting'] = 'meal_price'
        ctx.user_data['meal_price_id'] = meal_id
        await query.message.reply_text(f"💰 Taom ID #{meal_id} uchun yangi narx kiriting (so'm):")

    elif data.startswith('disc_'):
        meal_id = int(data.split('_')[1])
        ctx.user_data['awaiting'] = 'meal_discount'
        ctx.user_data['meal_discount_id'] = meal_id
        await query.message.reply_text(f"📝 Taom ID #{meal_id} uchun chegirma % kiriting (0-100):")

    elif data.startswith('del_'):
        meal_id = int(data.split('_')[1])
        await _delete_meal(meal_id)
        await query.answer("🗑 Taom o'chirildi!", show_alert=True)
        await staff_button_handler(update, ctx)

    # Aksiya management
    elif data.startswith('aksiya_off_'):
        aksiya_id = int(data.split('_')[2])
        active = await _toggle_aksiya(aksiya_id)
        msg_on = "✅ Yoqildi" if active else "❌ O'chirildi"
        await query.answer(msg_on, show_alert=True)
        await aksiyalar_handler(update, ctx)

    elif data == 'aksiya_add':
        meals = await _get_all_meals()
        kb = [[InlineKeyboardButton(m.name, callback_data=f"aksiya_meal_{m.id}")] for m in meals[:15]]
        await query.edit_message_text("🎁 Qaysi taomga aksiya qo'yasiz?", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith('aksiya_meal_'):
        meal_id = int(data.split('_')[2])
        ctx.user_data['aksiya_meal_id'] = meal_id
        ctx.user_data['awaiting'] = 'aksiya_discount'
        await query.message.reply_text(f"📝 Chegirma % kiriting (0-100):")


async def refresh_order_message(query, order_id, status, emoji, status_text):
    try:
        order, items = await _get_order_detail(order_id)
        if not order:
            return
        items_text = '\n'.join([f"  • {i.meal_name} x{i.quantity} — {i.price:,} UZS" for i in items])
        order_time = order.created_at.astimezone(pytz.timezone('Asia/Tashkent'))
        txt = (
            f"{emoji} <b>#{order.id}</b> [{status_text}]\n"
            f"👤 {order.full_name}\n📞 {order.phone}\n📍 {order.address}\n\n"
            f"{items_text}\n\n"
            f"💰 <b>Jami: {order.total_amount:,} UZS</b>\n"
            f"💳 {order.get_payment_method_display()}\n"
            f"🕐 {order_time.strftime('%d.%m.%Y %H:%M')} (Toshkent)"
        )
        kb = []
        if status == 'confirmed':
            kb.append([InlineKeyboardButton("🔥 Tayyorlanmoqda", callback_data=f"staff_cooking_{order.id}")])
        elif status == 'cooking':
            kb.append([InlineKeyboardButton("🚗 Yetkazilmoqda", callback_data=f"staff_delivering_{order.id}")])
        elif status == 'delivering':
            kb.append([InlineKeyboardButton("🏁 Bajarildi", callback_data=f"staff_done_{order.id}")])

        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb) if kb else None, parse_mode=ParseMode.HTML)
    except:
        pass


# ── Message handler (conversation flow) ──────────────────────────
async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text.strip()
    awaiting = ctx.user_data.get('awaiting')

    if awaiting == 'cat_name':
        await _create_category(text)
        await update.message.reply_text(f"✅ Kategoriya '{text}' qo'shildi!")
        ctx.user_data['awaiting'] = None

    elif awaiting == 'meal_name':
        ctx.user_data['temp_meal_name'] = text
        ctx.user_data['awaiting'] = 'meal_desc'
        await update.message.reply_text("📝 Taom haqida ma'lumot yuboring:")

    elif awaiting == 'meal_desc':
        ctx.user_data['temp_meal_desc'] = text
        ctx.user_data['awaiting'] = 'meal_price_input'
        await update.message.reply_text("💰 Narx kiriting (so'm):")

    elif awaiting == 'meal_price_input':
        try:
            price = int(text)
            ctx.user_data['temp_meal_price'] = price
            ctx.user_data['awaiting'] = 'meal_discount_input'
            await update.message.reply_text("📝 Chegirma % kiriting (0 bo'lsa 0 yuboring):")
        except:
            await update.message.reply_text("❌ Raqam kiriting!")

    elif awaiting == 'meal_discount_input':
        try:
            discount = int(text)
            cat_id = ctx.user_data.get('add_meal_cat', 1)
            meal = await _create_meal(
                ctx.user_data['temp_meal_name'],
                ctx.user_data['temp_meal_desc'],
                ctx.user_data['temp_meal_price'],
                cat_id,
                discount
            )
            await update.message.reply_text(f"✅ Taom '{meal.name}' qo'shildi! ID: {meal.id}")
            ctx.user_data['awaiting'] = None
            ctx.user_data.pop('temp_meal_name', None)
            ctx.user_data.pop('temp_meal_desc', None)
            ctx.user_data.pop('temp_meal_price', None)
        except:
            await update.message.reply_text("❌ Raqam kiriting!")

    elif awaiting == 'meal_price':
        try:
            price = int(text)
            meal_id = ctx.user_data['meal_price_id']
            await _update_meal_price(meal_id, price)
            await update.message.reply_text(f"✅ Narx yangilandi: {price:,} UZS")
            ctx.user_data['awaiting'] = None
        except:
            await update.message.reply_text("❌ Raqam kiriting!")

    elif awaiting == 'meal_discount':
        try:
            discount = int(text)
            meal_id = ctx.user_data['meal_discount_id']
            await _update_meal_discount(meal_id, discount)
            await update.message.reply_text(f"✅ Chegirma yangilandi: {discount}%")
            ctx.user_data['awaiting'] = None
        except:
            await update.message.reply_text("❌ Raqam kiriting!")

    elif awaiting == 'aksiya_discount':
        try:
            discount = int(text)
            ctx.user_data['temp_aksiya_discount'] = discount
            ctx.user_data['awaiting'] = 'aksiya_days'
            await update.message.reply_text("📅 Necha kun aksiya bo'lsin? (masalan: 7)")
        except:
            await update.message.reply_text("❌ Raqam kiriting!")

    elif awaiting == 'aksiya_days':
        try:
            days = int(text)
            meal_id = ctx.user_data['aksiya_meal_id']
            discount = ctx.user_data['temp_aksiya_discount']
            await _create_aksiya(meal_id, discount, days)
            meal = await sync_to_async(lambda: Meal.objects.get(id=meal_id))()
            await update.message.reply_text(f"✅ Aksiya qo'shildi: {meal.name} — {discount}% ({days} kun)")
            ctx.user_data['awaiting'] = None
        except:
            await update.message.reply_text("❌ Raqam kiriting!")


# ── Main ──────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", orders_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("menu", menu_manage_handler))
    app.add_handler(CommandHandler("aksiyalar", aksiyalar_handler))
    app.add_handler(CommandHandler("users", users_handler))
    app.add_handler(CommandHandler("add_aksiya", aksiyalar_handler))

    app.add_handler(MessageHandler(filters.Regex("^📦 Buyurtmalar$"), orders_handler))
    app.add_handler(MessageHandler(filters.Regex("^📊 Statistika$"), stats_handler))
    app.add_handler(MessageHandler(filters.Regex("^🍽 Menyu boshqarish$"), menu_manage_handler))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Aksiyalar$"), aksiyalar_handler))
    app.add_handler(MessageHandler(filters.Regex("^👥 Foydalanuvchilar$"), users_handler))

    app.add_handler(CallbackQueryHandler(staff_button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.add_error_handler(lambda u, ctx: logger.error(f"Error: {ctx.error}", exc_info=ctx.error))

    logger.info(f"👨‍💼 Staff Bot ishga tushdi!")
    logger.info(f"👑 Admin ID: {ADMIN_ID}")

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
