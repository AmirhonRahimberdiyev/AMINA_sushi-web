from django.db import models
from django.core.exceptions import BadRequest


class Xodim(models.Model):
    name = models.CharField(max_length=56)
    age = models.PositiveIntegerField(default=18)
    maosh = models.IntegerField(default=4000000)
    position = models.SmallIntegerField(default=1, choices=[
        (1, 'Kassir'), (2, 'Oshpaz'), (3, 'Manager'), (4, 'Farrosh'), (5, 'Director'),
    ])

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.age < 18:
            raise BadRequest('yoshi 18 dan kichik')
        return super().save(*args, **kwargs)


class Branch(models.Model):
    name = models.CharField(max_length=150)
    location = models.JSONField(default=dict)
    location_name = models.CharField(max_length=128)
    phone = models.CharField(max_length=20, default="+998901234567")
    manager = models.ForeignKey(Xodim, on_delete=models.SET_NULL, null=True,
                                  limit_choices_to={'position': 3})
    is_active = models.BooleanField(default=True, help_text="Filial buyurtma qabul qiladimi")
    bot_token = models.CharField(max_length=200, blank=True, default='', help_text="Filial uchun Telegram bot token (ixtiyoriy)")
    manager_chat_id = models.CharField(max_length=50, blank=True, default='', help_text="Manager Telegram chat ID (buyurtma bildirishnomasi uchun)")

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=56)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='ctgs/')

    def __str__(self):
        return self.name


class Meal(models.Model):
    name = models.CharField(max_length=56)
    description = models.TextField()
    price = models.PositiveIntegerField()
    ctg = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount = models.SmallIntegerField(default=0)

    def total_price(self):
        return self.price

    def get_final_price(self):
        aksiya = self.aksiya_set.filter(is_active=True).first()
        discount = aksiya.discount if aksiya else self.discount
        return int(self.price * (1 - discount / 100))

    def get_first_image(self):
        first = self.images.first()
        if first:
            return first.image.url
        return None

    def __str__(self):
        return self.name


class MealImage(models.Model):
    image = models.ImageField(upload_to='meals/')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return self.image.name


class Set(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.PositiveIntegerField()
    old_price = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='sets/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    items_description = models.TextField(default='', blank=True, help_text="Set tarkibi (masalan: 8 Salmon Nigiri + 6 California Roll + 2x Choy)")
    servings = models.PositiveIntegerField(default=1, help_text="Nechta kishilik (1, 2, 4)")
    preparation_time = models.CharField(max_length=50, default='', blank=True, help_text="Tayyorlanish vaqti (masalan: 20-30 daqiqa)")
    calories = models.PositiveIntegerField(default=0, help_text="Kaloriya miqdori")
    highlights = models.TextField(default='', blank=True, help_text="Alohida xususiyatlari (har qator bitta highlight)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_final_price(self):
        return self.price

    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int((self.old_price - self.price) / self.old_price * 100)
        return 0

    def get_first_image(self):
        first_image = self.images.first()
        if first_image:
            return first_image.image.url
        if self.image:
            return self.image.url
        return None

    def get_highlights_list(self):
        if not self.highlights:
            return []
        return [h.strip() for h in self.highlights.split('\n') if h.strip()]

    class Meta:
        ordering = ['-id']


class SetImage(models.Model):
    image = models.ImageField(upload_to='sets/')
    set = models.ForeignKey(Set, on_delete=models.CASCADE, related_name='images')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.set.name} - rasm {self.order}"

    class Meta:
        ordering = ['order']


class Aksiya(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    discount = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.meal.name} — {self.discount}%"


class TelegramUser(models.Model):
    tg_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} ({self.tg_id})"


class Order(models.Model):
    SOURCE_CHOICES = [
        ('web', 'Veb sayt'),
        ('telegram', 'Telegram Bot'),
        ('tg_webapp', 'Telegram Web App'),
    ]
    PAYMENT_CHOICES = [
        ('cash', 'Naqd pul'),
        ('card', 'Karta'),
        ('click', 'Click'),
        ('payme', 'Payme'),
    ]
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('confirmed', 'Tasdiqlangan'),
        ('cooking', 'Tayyorlanmoqda'),
        ('delivering', 'Yetkazilmoqda'),
        ('done', 'Bajarildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    total_amount = models.IntegerField(default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='web')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)

    def __str__(self):
        return f"#{self.id} {self.full_name} — {self.total_amount:,} so'm"

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    meal_name = models.CharField(max_length=100)
    price = models.IntegerField()
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.meal_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.price:
            meal = Meal.objects.filter(name=self.meal_name).first()
            if meal:
                self.price = meal.get_final_price()
        super().save(*args, **kwargs)

    def subtotal(self):
        return self.price * self.quantity


class DeliveryZone(models.Model):
    name = models.CharField(max_length=100, help_text="Hudud nomi (masalan: Yunusabad, Chilanzar)")
    min_order = models.PositiveIntegerField(default=0, help_text="Minimal buyurtma summasi (so'm)")
    delivery_fee = models.PositiveIntegerField(default=0, help_text="Yetkazib berish narxi (so'm)")
    estimated_time = models.CharField(max_length=50, default="30-45 daqiqa", help_text="Taxminiy yetkazib berish vaqti")
    description = models.TextField(default='', blank=True, help_text="Qo'shimcha ma'lumot")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Ko'rsatish tartibi")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']


class ChatSession(models.Model):
    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='chat_sessions', null=True, blank=True)
    tg_id = models.BigIntegerField(null=True, blank=True, help_text="Telegram user ID (agar TelegramUser bo'lmasa)")
    user_name = models.CharField(max_length=100, blank=True, default='')
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat: {self.user_name or self.tg_id} ({'ochiq' if self.is_open else 'yopiq'})"

    class Meta:
        ordering = ['-last_message_at']


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=20, choices=[
        ('user', 'Foydalanuvchi'),
        ('cashier', 'Kassir'),
    ])
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.sender}] {self.text[:50]}"

    class Meta:
        ordering = ['created_at']
