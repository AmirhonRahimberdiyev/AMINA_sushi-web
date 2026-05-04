from django.contrib import admin
from .models import *


# Inline: MealImages — Meals ichida rasm yuklash


class MealImageInline(admin.TabularInline):
    model = MealImage
    extra = 1
    max_num = 10


# Meal Admin
@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    inlines = [MealImageInline]
    list_display = ("name", "price", "discount", "get_final_price")
    search_fields = ("name",)
    list_filter = ("ctg",)

    def get_final_price(self, obj):
        return obj.get_final_price()
    get_final_price.short_description = "Chegirmali narx"


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


# Aksiya Admin
@admin.register(Aksiya)
class AksiyaAdmin(admin.ModelAdmin):
    list_display = ("meal", "discount", "start_date", "end_date", "is_active")
    search_fields = ("meal__name",)
    list_filter = ("is_active",)


# Branch Admin
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "location_name", "phone", "is_active", "manager")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    search_fields = ("name", "location_name")
    fieldsets = (
        ("Asosiy", {
            "fields": ("name", "location_name", "location", "phone", "manager", "is_active")
        }),
        ("Telegram Bot (Buyurtma bildirishnomalari uchun)", {
            "fields": ("bot_token", "manager_chat_id"),
            "description": "Bu filialga kelgan buyurtmalar shu bot orqali yuboriladi. Bot token @BotFather dan olish mumkin. Manager chat ID - buyurtmalar keladigan Telegram chat."
        }),
    )


# Xodim Admin
@admin.register(Xodim)
class XodimAdmin(admin.ModelAdmin):
    list_display = ("name", "age", "maosh", "position")
    search_fields = ("name",)
    list_filter = ("position",)


# Telegram User Admin
@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("tg_id", "username", "first_name", "phone", "created_at")
    search_fields = ("tg_id", "username", "first_name")


# OrderItem Inline — Order ichida itemlar ko‘rinadi
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ("subtotal",)


# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "total_amount", "status", "branch", "created_at")
    list_filter = ("status", "payment_method", "source", "branch")
    search_fields = ("full_name", "phone", "address")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at",)


# Oddiy registratsiya
@admin.register(MealImage)
class MealImageAdmin(admin.ModelAdmin):
    list_display = ("meal", "image")


class SetImageInline(admin.TabularInline):
    model = SetImage
    extra = 1
    max_num = 10
    fields = ('image', 'order')


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    inlines = [SetImageInline]
    list_display = ("name", "price", "old_price", "discount_percent", "servings", "is_active")
    search_fields = ("name", "description")
    list_filter = ("is_active", "servings")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("name", "description", "image", "is_active")
        }),
        ("Narx", {
            "fields": ("price", "old_price")
        }),
        ("Batafsil", {
            "fields": ("items_description", "servings", "preparation_time", "calories", "highlights"),
            "description": "Set tarkibi va xususiyatlari"
        }),
    )

    def discount_percent(self, obj):
        return f"-{obj.discount_percent()}%"
    discount_percent.short_description = "Chegirma"


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "min_order", "delivery_fee", "estimated_time", "is_active", "order")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("sender", "text", "created_at")
    can_delete = False
    max_num = 50
    ordering = ("-created_at",)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("user_name", "tg_id", "is_open", "last_message_at", "created_at")
    list_filter = ("is_open",)
    search_fields = ("user_name", "tg_id")
    inlines = [ChatMessageInline]
    readonly_fields = ("created_at", "last_message_at")