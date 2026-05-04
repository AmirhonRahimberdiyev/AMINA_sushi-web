from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Xodim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=56)),
                ('age', models.PositiveIntegerField(default=18)),
                ('maosh', models.IntegerField(default=4000000)),
                ('position', models.SmallIntegerField(choices=[(1, 'Kassir'), (2, 'Oshpaz'), (3, 'Manager'), (4, 'Farrosh'), (5, 'Director')], default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=56)),
                ('is_active', models.BooleanField(default=True)),
                ('image', models.ImageField(upload_to='ctgs/')),
            ],
        ),
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150)),
                ('location', models.JSONField(default=dict)),
                ('location_name', models.CharField(max_length=128)),
                ('manager', models.ForeignKey(limit_choices_to={'position': 3}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.xodim')),
            ],
        ),
        migrations.CreateModel(
            name='Meal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=56)),
                ('description', models.TextField(verbose_name="To'liq ma'lumot")),
                ('price', models.PositiveIntegerField()),
                ('discount', models.SmallIntegerField(default=0)),
                ('ctg', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.category')),
            ],
        ),
        migrations.CreateModel(
            name='MealImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to='meals/')),
                ('meal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='core.meal')),
            ],
        ),
        migrations.CreateModel(
            name='Aksiya',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('discount', models.IntegerField(default=0)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('meal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.meal')),
            ],
        ),
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('tg_id', models.BigIntegerField(unique=True)),
                ('username', models.CharField(blank=True, max_length=100, null=True)),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('full_name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=20)),
                ('address', models.TextField()),
                ('total_amount', models.IntegerField(default=0)),
                ('payment_method', models.CharField(choices=[('cash', 'Naqd pul'), ('card', 'Karta'), ('click', 'Click'), ('payme', 'Payme')], default='cash', max_length=10)),
                ('source', models.CharField(choices=[('web', 'Veb sayt'), ('telegram', 'Telegram Bot'), ('tg_webapp', 'Telegram Web App')], default='web', max_length=20)),
                ('status', models.CharField(choices=[('new', 'Yangi'), ('confirmed', 'Tasdiqlangan'), ('cooking', 'Tayyorlanmoqda'), ('delivering', 'Yetkazilmoqda'), ('done', 'Bajarildi'), ('cancelled', 'Bekor qilindi')], default='new', max_length=20)),
                ('is_delivered', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('telegram_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.telegramuser')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('meal_name', models.CharField(max_length=100)),
                ('price', models.IntegerField()),
                ('quantity', models.IntegerField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.order')),
            ],
        ),
    ]
