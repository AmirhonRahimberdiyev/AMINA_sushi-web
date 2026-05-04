#!/bin/bash
echo "⚙️  UMAMI loyihasini sozlash..."
echo ""

cd "$(dirname "$0")"

# Install dependencies
echo "📦 Kutubxonalar o'rnatilmoqda..."
pip install -r requirements.txt

cd resturant

# Migrate
echo "🗃️  Ma'lumotlar bazasi sozlanmoqda..."
python manage.py migrate

# Create superuser
echo ""
echo "👤 Admin foydalanuvchi yaratish (Enter bosib o'tkazishingiz mumkin):"
python manage.py createsuperuser --noinput --username admin --email admin@umami.uz 2>/dev/null || echo "Admin allaqachon mavjud."

# Set admin password
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
django.setup()
from django.contrib.auth.models import User
u, _ = User.objects.get_or_create(username='admin')
u.set_password('admin123')
u.is_staff = True
u.is_superuser = True
u.save()
print('Admin: login=admin, parol=admin123')
"

# Collect static
echo ""
echo "📁 Static fayllar yig'ilmoqda..."
python manage.py collectstatic --noinput 2>/dev/null

echo ""
echo "✅ Sozlash tugadi!"
echo ""
echo "🚀 Ishga tushirish:"
echo "   Server:  ./start_server.sh"
echo "   Bot:     ./start_bot.sh"
echo ""
echo "🔐 Admin panel: http://localhost:8000/admin"
echo "   Login: admin | Parol: admin123"
echo ""
echo "🤖 Bot: @amina_suhsi_order_bot"
echo "📲 Web App: http://localhost:8000/tg-app/"
