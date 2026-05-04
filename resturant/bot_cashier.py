#!/usr/bin/env python
"""
UMAMI Premium Sushi — Kassir Chat Bot
Bot: Kassir mijozlar bilan shu bot orqali gaplashadi
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
django.setup()

from django.conf import settings as dj_settings
from asgiref.sync import sync_to_async
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from core.models import ChatSession, ChatMessage, TelegramUser

logging.basicConfig(
    format='%(asctime)s — [CASHIER BOT] — %(levelname)s — %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = dj_settings.CASHIER_BOT_TOKEN
ADMIN_IDS = dj_settings.CASHIER_CHAT_ADMIN_IDS
USER_BOT_TOKEN = dj_settings.USER_BOT_TOKEN

reply_state = {}

@sync_to_async
def _get_chat_session(tg_id):
    return ChatSession.objects.filter(tg_id=tg_id, is_open=True).first()

@sync_to_async
def _save_chat_message(session, sender, text):
    return ChatMessage.objects.create(session=session, sender=sender, text=text)

@sync_to_async
def _get_tg_user(tg_id):
    try:
        return TelegramUser.objects.get(tg_id=tg_id)
    except:
        return None

@sync_to_async
def _get_unread_count(tg_id):
    session = ChatSession.objects.filter(tg_id=tg_id, is_open=True).first()
    if session:
        return ChatMessage.objects.filter(session=session, sender='user', is_read=False).count()
    return 0


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Bu bot faqat kassirlar uchun.")
        return

    await update.message.reply_html(
        "🏪 <b>AMINA Kassir Chat Bot</b>\n\n"
        "Mijozlar Mini App dan xabar yozganda, sizga shu bot orqali keladi.\n\n"
        "📋 Foydalanish:\n"
        "1️⃣ Xabar kelganda — shu xabarni <b>Reply</b> qiling va javob yozing\n"
        "2️⃣ Yoki \"Javob berish\" tugmasini bosing\n\n"
        "/chats — Ochik chatlar ro'yxati\n"
        "/active — Faol chatlar",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Statistika", callback_data="stats")
        ]])
    )


async def chats_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    from django.utils import timezone
    from datetime import timedelta
    sessions = ChatSession.objects.filter(is_open=True).order_by('-last_message_at')[:20]

    if not sessions:
        await update.message.reply_text("📭 Hozircha ochiq chatlar yo'q.")
        return

    text = "💬 <b>Ochik chatlar</b>\n\n"
    keyboard = []
    for s in sessions:
        name = s.user_name or "Anonim"
        last_msg = s.messages.order_by('-created_at').first()
        last_text = last_msg.text[:30] + '...' if last_msg and len(last_msg.text) > 30 else (last_msg.text if last_msg else '')
        time_ago = ""
        if last_msg:
            diff = timezone.now() - last_msg.created_at
            minutes = int(diff.total_seconds() / 60)
            if minutes < 1:
                time_ago = "hozir"
            elif minutes < 60:
                time_ago = f"{minutes} daq oldin"
            else:
                time_ago = f"{minutes//60} soat oldin"

        text += f"👤 {name} (ID: {s.tg_id})\n💬 {last_text}\n🕐 {time_ago}\n\n"
        keyboard.append([InlineKeyboardButton(f"💬 {name}", callback_data=f"cashier_open_{s.tg_id}")])

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


async def cashier_open_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id_str = query.data.replace('cashier_open_', '')

    try:
        tg_id = int(chat_id_str)
    except ValueError:
        session_id = int(chat_id_str.replace('anon_', ''))
        from core.models import ChatSession
        session = ChatSession.objects.get(id=session_id)
        tg_id = session.tg_id
        if tg_id is None:
            tg_id = chat_id_str

    session = await _get_chat_session(tg_id)
    if not session and chat_id_str.startswith('anon_'):
        from core.models import ChatSession
        session_id = int(chat_id_str.replace('anon_', ''))
        session = ChatSession.objects.filter(id=session_id).first()

    if not session:
        await query.edit_message_text("Chat topilmadi.")
        return

    tg_user = await _get_tg_user(tg_id) if isinstance(tg_id, int) else None
    name = session.user_name or (tg_user.first_name if tg_user else "Anonim")

    messages = ChatMessage.objects.filter(session=session).order_by('-created_at')[:30]
    messages = reversed(list(messages))

    text = f"💬 <b>Chat: {name}</b> (ID: {chat_id_str})\n\n"
    keyboard = [[InlineKeyboardButton("↩️ Javob yozish", callback_data=f"cr_{chat_id_str}")]]

    for m in messages:
        sender_icon = "🏪" if m.sender == 'cashier' else "👤"
        text += f"{sender_icon} {m.text}\n"

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


async def cashier_reply_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        chat_id_str = query.data.replace('cr_', '')
        logger.info(f"Javob tugmasi bosildi: cr_{chat_id_str}")
        await query.answer()

        try:
            tg_id = int(chat_id_str)
        except ValueError:
            session_id = int(chat_id_str.replace('anon_', ''))
            from core.models import ChatSession
            session = ChatSession.objects.get(id=session_id)
            tg_id = session.tg_id if session.tg_id else chat_id_str

        session = await _get_chat_session(tg_id)
        if session:
            name = session.user_name or "Foydalanuvchi"
        else:
            name = "Foydalanuvchi"

        reply_state[query.from_user.id] = (tg_id, name)
        logger.info(f"Reply state set: cashier={query.from_user.id} -> {tg_id} ({name})")
        await query.edit_message_text(
            f"✏️ <b>{name}</b> (ID: {chat_id_str}) ga javob yozing.\n\nEndi xabaringizni yuboring:",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"cashier_reply_btn xatosi: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await query.answer(f"Xatolik: {e}", show_alert=True)


async def cashier_send_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Kassir javob xabari — avtomatik ID aniqlash"""
    cashier_id = update.effective_user.id
    text = update.message.text
    if not text or not text.strip():
        return

    user_id = None
    user_name = "Foydalanuvchi"

    reply_to = update.message.reply_to_message
    if reply_to and reply_to.text:
        import re
        match = re.search(r'ID:\s*(\S+)', reply_to.text)
        if match:
            user_id = match.group(1)

    if not user_id and cashier_id in reply_state:
        user_id, user_name = reply_state.pop(cashier_id)

    if not user_id:
        return

    try:
        actual_tg_id = int(user_id)
    except ValueError:
        actual_tg_id = user_id

    session = await _get_chat_session(actual_tg_id)
    if not session and isinstance(user_id, str) and user_id.startswith('anon_'):
        from core.models import ChatSession
        session_id = int(user_id.replace('anon_', ''))
        session = ChatSession.objects.filter(id=session_id).first()
        actual_tg_id = session.tg_id if session and session.tg_id else user_id

    if session:
        await _save_chat_message(session, 'cashier', text)

    try:
        if isinstance(actual_tg_id, int):
            await ctx.bot.send_message(
                chat_id=actual_tg_id,
                text=f"🏪 <b>Kassir javobi:</b>\n\n{text}",
                parse_mode=ParseMode.HTML,
            )
        await update.message.reply_text("✅ Javob yuborildi!")
    except Exception as e:
        logger.error(f"Javob yuborish xatosi: {e}")
        await update.message.reply_text(f"❌ Xatolik: foydalanuvchi botni bloklagan")


async def user_message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Yangi foydalanuvchi xabari (kassirga ko'rsatish)"""
    user = update.effective_user
    text = update.message.text
    if not text or not text.strip():
        return

    tg_user = await _get_tg_user(user.id)
    user_name = tg_user.first_name if tg_user else user.first_name

    session, _ = ChatSession.objects.get_or_create(
        tg_id=user.id,
        is_open=True,
        defaults={'user_name': user_name}
    )
    await _save_chat_message(session, 'user', text)

    cashier_msg = f"💬 <b>Yangi xabar</b>\n\n👤 {user_name or 'Anonim'}\n🆔 ID: {user.id}\n💬 {text}\n\n↩️ Javob berish: shu xabarni Reply qiling"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"↩️ Javob berish", callback_data=f"cr_{user.id}")
    ]])

    for admin_id in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                chat_id=admin_id,
                text=cashier_msg,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga yuborish xatosi: {e}")


async def stats_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    from django.db.models import Count
    total_sessions = ChatSession.objects.filter(is_open=True).count()
    total_messages = ChatMessage.objects.count()

    text = f"📊 <b>Statistika</b>\n\n"
    text += f"💬 Ochik chatlar: {total_sessions}\n"
    text += f"📨 Jami xabarlar: {total_messages}\n"
    text += f"👥 Adminlar: {len(ADMIN_IDS)}"

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    await update.message.reply_text("Buyruq tushunarsiz. /start yoki /chats bosing.")


def main():
    if not TOKEN:
        logger.error("CASHIER_BOT_TOKEN sozlanmagan!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chats", chats_handler))
    app.add_handler(CommandHandler("active", chats_handler))

    app.add_handler(CallbackQueryHandler(cashier_open_chat, pattern=r'^cashier_open_'))
    app.add_handler(CallbackQueryHandler(cashier_reply_btn, pattern=r'^cr_'))
    app.add_handler(CallbackQueryHandler(stats_handler, pattern=r'^stats'))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cashier_send_reply))

    app.add_error_handler(lambda u, ctx: logger.error(f"Error: {ctx.error}", exc_info=ctx.error))

    logger.info("🏪 Kassir Chat Bot ishga tushdi!")
    logger.info(f"👥 Admin IDs: {ADMIN_IDS}")

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
