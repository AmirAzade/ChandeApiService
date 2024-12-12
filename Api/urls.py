from django.urls import path
from .views  import currency_price, history_price, currency_price_old

urlpatterns = [
    path('currency/', currency_price, name='currency'),
    path('history/', history_price, name='history'),
    path('old/', currency_price_old, name='old'),
]
