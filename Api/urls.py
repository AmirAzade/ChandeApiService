from django.urls import path
from .views  import currency_price, history_price

urlpatterns = [
    path('currency/', currency_price, name='currency'),
    path('history/', history_price, name='history'),
]
