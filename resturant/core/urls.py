from django.urls import path
from . import views

urlpatterns = [
    path('', views.asosiy, name='asosiy'),
    path('menyu/', views.menyu, name='menyu'),
    path('filiallar/', views.filiallar, name='filiallar'),
    path('aksiyalar/', views.aksiyalar, name='aksiyalar'),
    path('delivery/', views.delivery, name='delivery'),
    path('cart/', views.cart, name='cart'),
    path('cart/order/', views.create_order, name='create_order'),
    path('tg-app/', views.tg_webapp, name='tg_webapp'),
    path('webhook/', views.webhook, name='webhook'),
    path('api/meals/', views.api_meals, name='api_meals'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/delivery-zones/', views.api_delivery_zones, name='api_delivery_zones'),
    path('api/chat/send/', views.api_chat_send, name='api_chat_send'),
    path('api/chat/history/', views.api_chat_history, name='api_chat_history'),
]
