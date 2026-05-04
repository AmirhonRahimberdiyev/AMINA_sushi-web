from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
import pytz
from .models import *
import json
import requests


def send_telegram_notification(order, items):
    """Branch ga qarab Telegram xabar yuborish"""
    payment_icons = {
        'cash': '💵 Naqd',
        'card': '💳 Karta',
        'click': '📱 Click',
        'payme': '💎 Payme',
    }
    source_icons = {
        'web': '🌐 Veb sayt',
        'telegram': '🤖 Telegram Bot',
        'tg_webapp': '📲 Telegram Web App',
    }

    items_text = '\n'.join([
        f"  • {item['name']} x{item.get('qty', 1)} — {int(item['price']):,} so'm"
        for item in items
    ])

    branch_info = ""
    if order.branch:
        branch_info = f"🏪 <b>Filial:</b> {order.branch.name}\n"

    # Tashkent vaqtini olish
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    order_time = order.created_at.astimezone(tashkent_tz)

    msg = (
        f"🍣 <b>YANGI BUYURTMA #{order.id}</b>\n\n"
        f"👤 <b>{order.full_name}</b>\n"
        f"📞 {order.phone}\n"
        f"📍 {order.address}\n"
        f"{branch_info}"
        f"🛒 <b>Buyurtma:</b>\n{items_text}\n\n"
        f"💰 <b>Jami: {order.total_amount:,} so'm</b>\n"
        f"💳 To'lov: {payment_icons.get(order.payment_method, order.payment_method)}\n"
        f"📌 Manba: {source_icons.get(order.source, order.source)}\n"
        f"🕐 Vaqt: {order_time.strftime('%d.%m.%Y %H:%M')} (Toshkent)"
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Tasdiqlash", "callback_data": f"confirm_{order.id}"},
            {"text": "❌ Bekor", "callback_data": f"cancel_{order.id}"},
        ]]
    }

    # Agar branch da bot_token va manager_chat_id bo'lsa — shu bot orqali yuborish
    target_chat = settings.ADMIN_CHAT_ID
    token = settings.STAFF_BOT_TOKEN
    
    if order.branch and order.branch.manager_chat_id:
        target_chat = order.branch.manager_chat_id
        # Agar branchning o'z bot_tokeni bo'lsa, shundan foydalanamiz
        if order.branch.bot_token:
            token = order.branch.bot_token
    try:
        resp = requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={
                'chat_id': target_chat,
                'text': msg,
                'parse_mode': 'HTML',
                'reply_markup': keyboard,
            },
            timeout=10
        )
        result = resp.json()
        if not result.get('ok'):
            print(f"Telegram xatosi: {result}")
        else:
            print(f"Telegram xabar yuborildi: chat={target_chat}, msg_id={result['result']['message_id']}")
    except Exception as e:
        print(f"Telegram xatosi: {e}")


def asosiy(request):
    sets = Set.objects.filter(is_active=True)
    return render(request, 'asosiy.html', {'sets': sets})


def menyu(request):
    meals = Meal.objects.select_related('ctg').prefetch_related('images').all()
    categories = Category.objects.filter(is_active=True)
    sets = Set.objects.filter(is_active=True)
    return render(request, 'menyu.html', {'meals': meals, 'categories': categories, 'sets': sets})


def filiallar(request):
    branches = Branch.objects.select_related('manager').all()
    return render(request, 'filiallar.html', {'branches': branches})


def aksiyalar(request):
    active_aksiyalar = (
        Aksiya.objects
        .filter(is_active=True)
        .select_related('meal', 'meal__ctg')
        .prefetch_related('meal__images')
        .order_by('-id')
    )
    return render(request, 'aksiyalar.html', {'aksiyalar': active_aksiyalar})


def cart(request):
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'cart.html', {'branches': branches})


def tg_webapp(request):
    """Telegram Web App uchun alohida sahifa"""
    meals = Meal.objects.select_related('ctg').prefetch_related('images').all()
    categories = Category.objects.filter(is_active=True)
    branches = Branch.objects.all()
    active_aksiyalar = (
        Aksiya.objects
        .filter(is_active=True)
        .select_related('meal', 'meal__ctg')
        .prefetch_related('meal__images')
        .order_by('-id')
    )
    sets = Set.objects.filter(is_active=True)
    delivery_zones = DeliveryZone.objects.filter(is_active=True)
    base_url = request.build_absolute_uri('/').rstrip('/')
    return render(request, 'tg_webapp.html', {
        'meals': meals,
        'categories': categories,
        'branches': branches,
        'aksiyalar': active_aksiyalar,
        'sets': sets,
        'delivery_zones': delivery_zones,
        'base_url': base_url,
    })


@csrf_exempt
def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()
        total_amount = int(data.get('total_amount', 0))
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'cash')
        source = data.get('source', 'web')
        tg_id = data.get('tg_id')
        branch_id = data.get('branch_id')

        if not name or not phone or not address or not items:
            return JsonResponse({'success': False, 'error': "Barcha maydonlarni to'ldiring"})

        branch = None
        if branch_id:
            branch = Branch.objects.filter(id=branch_id, is_active=True).first()

        tg_user = None
        if tg_id:
            tg_user, _ = TelegramUser.objects.get_or_create(
                tg_id=tg_id,
                defaults={'first_name': name}
            )

        order = Order.objects.create(
            full_name=name,
            phone=phone,
            address=address,
            total_amount=total_amount,
            payment_method=payment_method,
            source=source,
            branch=branch,
            telegram_user=tg_user,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                meal_name=item.get('name', ''),
                price=int(item.get('price', 0)),
                quantity=int(item.get('qty', 1)),
            )

        send_telegram_notification(order, items)

        return JsonResponse({'success': True, 'order_id': order.id})

    except Exception as e:
        print(f"Order xatosi: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def webhook(request):
    """Telegram webhook uchun"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            callback = data.get('callback_query')
            if callback:
                cb_data = callback.get('data', '')
                chat_id = callback['message']['chat']['id']
                token = settings.STAFF_BOT_TOKEN

                if cb_data.startswith('confirm_'):
                    order_id = int(cb_data.replace('confirm_', ''))
                    Order.objects.filter(id=order_id).update(status='confirmed')
                    user_token = settings.USER_BOT_TOKEN
                    requests.post(
                        f'https://api.telegram.org/bot{user_token}/answerCallbackQuery',
                        json={'callback_query_id': callback['id'], 'text': f'✅ Buyurtma #{order_id} tasdiqlandi!'}
                    )
                elif cb_data.startswith('cancel_'):
                    order_id = int(cb_data.replace('cancel_', ''))
                    Order.objects.filter(id=order_id).update(status='cancelled')
                    user_token = settings.USER_BOT_TOKEN
                    requests.post(
                        f'https://api.telegram.org/bot{user_token}/answerCallbackQuery',
                        json={'callback_query_id': callback['id'], 'text': f'❌ Buyurtma #{order_id} bekor qilindi'}
                    )
        except Exception as e:
            print(f"Webhook xatosi: {e}")
    return JsonResponse({'ok': True})


def api_meals(request):
    """Bot uchun API"""
    meals = []
    for meal in Meal.objects.select_related('ctg').prefetch_related('images').all():
        meals.append({
            'id': meal.id,
            'name': meal.name,
            'description': meal.description,
            'price': meal.total_price(),
            'original_price': meal.price,
            'discount': meal.discount,
            'category': meal.ctg.name,
            'category_id': meal.ctg.id,
            'image': request.build_absolute_uri(meal.get_first_image()) if meal.get_first_image() else '',
        })
    return JsonResponse({'meals': meals})


def api_categories(request):
    cats = [{'id': c.id, 'name': c.name} for c in Category.objects.filter(is_active=True)]
    return JsonResponse({'categories': cats})


def delivery(request):
    """Yetkazib berish sahifasi (web sayt uchun)"""
    zones = DeliveryZone.objects.filter(is_active=True)
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'delivery.html', {'zones': zones, 'branches': branches})


@csrf_exempt
def api_delivery_zones(request):
    """Yetkazib berish hududlari API"""
    zones = DeliveryZone.objects.filter(is_active=True)
    data = []
    for z in zones:
        data.append({
            'id': z.id,
            'name': z.name,
            'min_order': z.min_order,
            'delivery_fee': z.delivery_fee,
            'estimated_time': z.estimated_time,
            'description': z.description,
        })
    return JsonResponse({'zones': data})


@csrf_exempt
def api_chat_send(request):
    """Foydalanuvchi xabar yuboradi — Kassir botiga yuboriladi"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})

    try:
        data = json.loads(request.body)
        tg_id = data.get('tg_id')
        user_name = data.get('name', '')
        text = data.get('text', '').strip()

        if not text:
            return JsonResponse({'success': False, 'error': "Xabar bo'sh"})

        tg_user = None
        if tg_id:
            tg_user, _ = TelegramUser.objects.get_or_create(
                tg_id=tg_id,
                defaults={'first_name': user_name}
            )

        session, _ = ChatSession.objects.get_or_create(
            tg_id=tg_id,
            is_open=True,
            defaults={
                'telegram_user': tg_user,
                'user_name': user_name,
            }
        )
        session.user_name = user_name or session.user_name
        session.save()

        msg = ChatMessage.objects.create(
            session=session,
            sender='user',
            text=text,
        )

        token = settings.CASHIER_BOT_TOKEN
        admin_ids = settings.CASHIER_CHAT_ADMIN_IDS

        chat_id = tg_id if tg_id else f"anon_{session.id}"
        cashier_msg = f"💬 <b>Yangi xabar</b>\n\n👤 {user_name or 'Anonim'}\n🆔 ID: {chat_id}\n💬 {text}\n\n↩️ Javob berish: shu xabarni Reply qiling"
        reply_keyboard = {
            "inline_keyboard": [[
                {"text": f"↩️ Javob berish (ID: {chat_id})", "callback_data": f"cr_{chat_id}"}
            ]]
        }
        for admin_id in admin_ids:
            try:
                requests.post(
                    f'https://api.telegram.org/bot{token}/sendMessage',
                    json={
                        'chat_id': admin_id,
                        'text': cashier_msg,
                        'parse_mode': 'HTML',
                        'reply_markup': reply_keyboard,
                    },
                    timeout=10
                )
            except Exception as e:
                print(f"Telegram chat error (admin {admin_id}): {e}")

        return JsonResponse({'success': True, 'message_id': msg.id, 'created_at': msg.created_at.isoformat()})

    except Exception as e:
        print(f"Chat send error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def api_chat_history(request):
    """Chat tarixini olish"""
    tg_id = request.GET.get('tg_id')
    if not tg_id:
        return JsonResponse({'success': False, 'error': 'tg_id required'})

    try:
        session = ChatSession.objects.filter(tg_id=int(tg_id)).first()
        if not session:
            return JsonResponse({'messages': [], 'unread': 0})

        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        data = []
        for m in messages:
            data.append({
                'id': m.id,
                'sender': m.sender,
                'text': m.text,
                'created_at': m.created_at.isoformat(),
            })

        unread = ChatMessage.objects.filter(session=session, sender='cashier', is_read=False).count()
        ChatMessage.objects.filter(session=session, sender='cashier').update(is_read=True)

        return JsonResponse({'messages': data, 'unread': unread})

    except Exception as e:
        print(f"Chat history error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
