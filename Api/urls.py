from django.urls import path
from .views  import currency_price, history_price, currency_price_old, upload_to_telegram

urlpatterns = [
    path('currency/', currency_price, name='currency'),
    path('history/', history_price, name='history'),
    path('old/', currency_price_old, name='old'),
    # path('download/<str:target_file_name>/', telegramdl, name='download_file_from_telegram'),
    path('upload/', upload_to_telegram, name='upload_to_telegram'),
]
