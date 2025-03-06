from django.http import JsonResponse
from .calculateFiles.bonbast import get_prices_from_api
from .calculateFiles.token_manager import TokenManager
from django.core.cache import cache
from .bonbast.server import get_history, get_graph_data
from .bonbast.helpers.utils import filter_valids, convert_json
from datetime import datetime, timedelta
import json
from collections import OrderedDict
import calendar

from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument
from django.http import HttpResponse
from django.conf import settings
import requests
import re

from requests.structures import CaseInsensitiveDict

def convert_to_date_yesterday(date_str):
    dt = datetime.strptime(date_str, "%B %d, %Y %H:%M")
    yesterday = dt - timedelta(days=1)
    return datetime(yesterday.year, yesterday.month, yesterday.day)

def convert_to_date(date_str):
    dt = datetime.strptime(date_str, "%B %d, %Y %H:%M")
    return datetime(dt.year, dt.month, dt.day)

def dist_calculate(json1, json2):
    for currency_code, values in json2.items():
        currency1_key = f"{currency_code}1"
        currency2_key = f"{currency_code}2"

        if currency1_key in json1 and "sell" in values:
            json1[f"{currency_code}3"] = str(int(json1[currency1_key]) - values["sell"])
        elif currency2_key in json1 and "sell" in values:
            json1[f"{currency_code}3"] = str(int(json1[currency2_key]) - values["sell"])

    # Return json1 as a dictionary, not as a JSON string
    return json1

def convert_currency_data(input_data):
    output = {"data": []}

    for key in input_data.keys():
        if key == 'mithqal' or key == 'ounce' or key == 'gol18':
            history_price = get_history_price(key, input_data['last_modified'])

            currency_entry = {
                "symbol": key.upper(),
                "name": "",  # Add logic here to map symbols to names if available
                "sell": int(float(input_data[key])),
                "buy": int(float(input_data[key])),
                "change": None,
                "history": history_price
            }
            output["data"].append(currency_entry)
        if key.endswith("1"):
            currency_code = key[:-1]
            # print('*', currency_code)
            buy_price_key = f"{currency_code}1"
            sell_price_key = f"{currency_code}2"
            change_price_key = f"{currency_code}3"
            history_price = get_history_price(currency_code, input_data['last_modified'])

            if buy_price_key in input_data and sell_price_key in input_data and change_price_key in input_data:
                currency_entry = {
                    "symbol": currency_code.upper(),
                    "name": "",  # Add logic here to map symbols to names if available
                    "sell": int(input_data[sell_price_key]),
                    "buy": int(input_data[buy_price_key]),
                    "change": int(input_data[change_price_key]),
                    "history": history_price
                }

                output["data"].append(currency_entry)

    return output


def get_history_price(currency_symbol, date_string):
    history_symbol = f'{currency_symbol}_history'
    values_list = cache.get(history_symbol)

    if values_list is None:
        specific_date = convert_to_date_yesterday(date_string)
        end_date = specific_date
        start_date_helper = specific_date - timedelta(days=6)
        start_date = datetime(start_date_helper.year, start_date_helper.month, start_date_helper.day)



        result = get_graph_data(currency_symbol.lower(), start_date, end_date)
        values_list_helper = list(map(lambda x: x[1], result.items()))
        values_list = values_list_helper[-6:]

        cache.set(history_symbol, values_list, 24*60*60)

    return values_list


# new function for bon-bast.com
def convert_currency_json(data):
    response = {"data": []}
    
    for symbol, buy_price in data.items():
        show_symbol = symbol
        if symbol.upper() == "SEKKEH":
            show_symbol = "emami1"
        elif symbol.upper() == "BAHAR":
            show_symbol = "azadi1"
        elif symbol.upper() == "NIM":
            show_symbol = "azadi1_2"
        elif symbol.upper() == "ROB":
            show_symbol = "azadi1_4"
        elif symbol.upper() == "GERAMI":
            show_symbol = "azadi1g"
        elif symbol.upper() == "USD_XAU":
            show_symbol = "ounce"
        elif symbol.upper() == "XAU":
            continue
        elif symbol.upper() == "ABSHODEH":
            show_symbol = "mithqal"
        elif symbol.upper() == "18AYAR":
            show_symbol = "gol18"
        elif symbol.upper() == "BTC_USDT":
            continue

        response["data"].append({
            "symbol": show_symbol.upper(),
            "buy": float(buy_price),
            "sell": float(buy_price),
            "change": 0,
            "history": [0, 0, 0, 0, 0, 0]  # Example history
        })
    
    return response

def extract_symbols_data(html_content):
    match = re.search(r'var symbolsData=(\{.*?\});', html_content, re.DOTALL)
    if match:
        json_data = match.group(1)
        try:
            symbols_data = json.loads(json_data)
            return symbols_data
        except json.JSONDecodeError:
            return None
    else:
        return None

def get_new_prices():
    try:
        url = "https://www.bon-bast.com"
        response = requests.get(url)
        
        response.raise_for_status()
        
        symbols_data = extract_symbols_data(response.text)
        if symbols_data:
            validFormat = convert_currency_json(symbols_data)
            # print(json.dumps(symbols_data, indent=2))
            return json.dumps(validFormat, indent=2)
            # file.write(json.dumps(validFormat, indent=2))

    except requests.exceptions.RequestException as e:
        return None

# end of new function for bon-bast.com

# new functions to use alanChand as source
valid_symbols = [
    'USD',
    'EUR',
    'GBP',
    'CHF',
    'CAD',
    'AUD',
    'SEK',
    'NOK',
    'RUB',
    'THB',
    'SGD',
    'HKD',

    'AZN',
    'AMD',
    'DKK',
    'AED',
    'JPY',
    'TRY',
    'CNY',
    'SAR',
    'INR',
    'MYR',
    'AFN',
    'KWD',
    'IQD',
    'BHD',
    'OMR',
    'QAR',
]

valid_golds = {
    'ABSHODEH': 'mithqal',
    '18AYAR': 'gol18',
    'USD_XAU': 'ounce',
    'SEKKEH': 'emami1',
    'BAHAR': 'azadi1',
    'NIM': 'azadi1_2',
    'ROB': 'azadi1_4',
    'SEK': 'azadi1g'
}

def transform_currency_data(input_json_currency, input_json_golds):
    output_data = {"data": []}
    
    for currency in input_json_currency["arz"]:
        symbol = currency["slug"].upper()
        
        if not symbol in valid_symbols:
            continue

        # Extracting the latest price and history
        price_entries = sorted(currency["price"], key=lambda x: x["created_at"], reverse=True)
        
        if price_entries:
            latest_price = price_entries[0]
            buy_price = latest_price["price"]  # Assuming buy price is slightly lower
            sell_price = latest_price["price"]
            change = price_entries[0]["price"] - price_entries[1]["price"] if len(price_entries) > 1 else 0

            price_entries.reverse()

            history = [entry["price"] for entry in price_entries[:2]]
            while len(history) < 7:
                history.insert(0, 0)

            
            output_data["data"].append({
                "symbol": symbol,
                "buy": round(buy_price),
                "sell": round(sell_price),
                "change": round(change, 1),
                "history": history
            })


    for currency in input_json_golds["gold"]:
        symbol = currency["slug"].upper()
        
        if not symbol in valid_golds:
            continue

        # Extracting the latest price and history
        price_entries = sorted(currency["price"], key=lambda x: x["created_at"], reverse=True)
        
        if price_entries:
            latest_price = price_entries[0]
            buy_price = latest_price["price"]  # Assuming buy price is slightly lower
            sell_price = latest_price["price"]
            change = price_entries[0]["price"] - price_entries[1]["price"] if len(price_entries) > 1 else 0

            price_entries.reverse()

            history = [entry["price"] for entry in price_entries[:2]]
            while len(history) < 7:
                history.insert(0, 0)

            
            output_data["data"].append({
                "symbol": valid_golds[symbol],
                "buy": round(buy_price),
                "sell": round(sell_price),
                "change":  round(change, 1),
                "history": history
            })


    
    return output_data


def get_prices_from_alanChand():
    url_currency = "https://admin.alanchand.com/api/arz"
    url_gold = "https://admin.alanchand.com/api/gold"

    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"
    data = '{"lang":"fa"}'

    resp_currency = requests.post(url_currency, headers=headers, data=data).json()
    resp_gold = requests.post(url_gold, headers=headers, data=data).json()

    transformed_data = transform_currency_data(resp_currency, resp_gold)
    return json.dumps(transformed_data, indent=2, ensure_ascii=False)
# end of new functions to use alanChand as source

def currency_price(request):

    cache_timeout = 120
    shirini_status = False

    currency_price_cache = cache.get('currency_price')

    if currency_price_cache is None:
        # token_manager = TokenManager()
        # token = token_manager.generate()
        # current_prices = get_prices_from_api(token.value) #important

        # current_prices = {k if k != 'azadi1' else 'azadi11': v for k, v in current_prices.items()}
        # current_prices = {k if k != 'azadi1_2' else 'azadi1_21': v for k, v in current_prices.items()}
        # current_prices = {k if k != 'azadi1_4' else 'azadi1_41': v for k, v in current_prices.items()}
        # current_prices = {k if k != 'azadi1g' else 'azadi1g1': v for k, v in current_prices.items()}
        # current_prices = {k if k != 'emami1' else 'emami11': v for k, v in current_prices.items()}

        # specific_date = convert_to_date_yesterday(current_prices['last_modified'])

        # yesterday_price_cache = cache.get(str(specific_date))

        # if yesterday_price_cache is None:
        #     currencies_list, coins_list = get_history(specific_date)
        #     currencies_list, coins_list = filter_valids(currencies_list, coins_list)

        #     yesterday_prices = convert_json(currencies_list, coins_list)
        #     cache.set(str(specific_date), yesterday_prices, 24*60*60)
        # else:
        #     yesterday_prices = yesterday_price_cache

        # final_json = dist_calculate(current_prices, yesterday_prices)

        sorted_final_json = json.loads(get_prices_from_alanChand())
        sorted_final_json = OrderedDict(sorted(sorted_final_json.items()))
        sorted_final_json["shirini"] = shirini_status

        # sorted_final_json = convert_currency_data(sorted_final_json)
        cache.set('currency_price', sorted_final_json, cache_timeout)

        return JsonResponse(sorted_final_json, status=200)


    else:
        return JsonResponse(currency_price_cache, status=200)
    
def currency_price_old(request):
    cache_timeout = 10
    shirini_status = False

    currency_price_cache = cache.get('currency_price')

    if currency_price_cache is None:
        token_manager = TokenManager()
        token = token_manager.generate()
        current_prices = get_prices_from_api(token.value) #important

        current_prices = {k if k != 'azadi1' else 'azadi11': v for k, v in current_prices.items()}
        current_prices = {k if k != 'azadi1_2' else 'azadi1_21': v for k, v in current_prices.items()}
        current_prices = {k if k != 'azadi1_4' else 'azadi1_41': v for k, v in current_prices.items()}
        current_prices = {k if k != 'azadi1g' else 'azadi1g1': v for k, v in current_prices.items()}
        current_prices = {k if k != 'emami1' else 'emami11': v for k, v in current_prices.items()}

        specific_date = convert_to_date_yesterday(current_prices['last_modified'])

        yesterday_price_cache = cache.get(str(specific_date))

        if yesterday_price_cache is None:
            currencies_list, coins_list = get_history(specific_date)
            currencies_list, coins_list = filter_valids(currencies_list, coins_list)

            yesterday_prices = convert_json(currencies_list, coins_list)
            cache.set(str(specific_date), yesterday_prices, 24*60*60)
        else:
            yesterday_prices = yesterday_price_cache

        final_json = dist_calculate(current_prices, yesterday_prices)
        sorted_final_json = OrderedDict(sorted(final_json.items()))
        sorted_final_json["shirini"] = shirini_status

        cache.set('currency_price', sorted_final_json, cache_timeout)

        return JsonResponse(sorted_final_json, status=200)


    else:
        return JsonResponse(currency_price_cache, status=200)

def history_price(request):
    specific_date = datetime(2024, 11, 7)
    currencies_list, coins_list = get_history(specific_date)
    currencies_list, coins_list = filter_valids(currencies_list, coins_list)

    res = convert_json(currencies_list, coins_list)
    return JsonResponse(res, status=200)

# api_id = '29521119'
# api_hash = '885aa49d84d2e1d5e95095377e0afb29'

# def telegramdl(request, target_file_name):
#     # Define the chat name (you can change this to any chat or Saved Messages)
#     chat_name = "AmirrAzade"  # Specify the chat/channel name where the file is uploaded
    
#     # Initialize the Telegram client
#     with TelegramClient('session_name', api_id, api_hash) as client:
#         # Get the messages from the specified chat/channel (limit to 100 messages)
#         messages = client.get_messages(chat_name, limit=100)
#         print("**************************************************")
#         print("**************************************************")
#         print(messages)
#         print("**************************************************")
#         print("**************************************************")
#         print("**************************************************")

#         for message in messages:
#             # Check if the message contains a file (document or media)
#             if message.file:
#                 # Check if it's a document and matches the file name
#                 if isinstance(message.media, InputMessagesFilterDocument) and target_file_name.lower() in message.file.name.lower():
#                     # Download the file to a temporary location
#                     file_path = message.download_media(file=target_file_name)
#                     print(f"Downloaded file: {file_path}")
                    
#                     # Open the downloaded file and send it as an HTTP response
#                     with open(file_path, 'rb') as f:
#                         response = HttpResponse(f.read(), content_type="application/octet-stream")
#                         response['Content-Disposition'] = f'attachment; filename={target_file_name}'
#                         return response
        
#         # If the file is not found
#         return HttpResponse(f"File '{target_file_name}' not found.", status=404)
    
import os
import tempfile
from django.shortcuts import render
from django.http import HttpResponse
from .forms import FileUploadForm
# from telegram_upload.client import TelegramClient

from django.conf import settings

def upload_to_telegram(request):
    print(settings.TEMPLATES)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponse("File uploaded successfully!")
    else:
        form = FileUploadForm()

    return render(request, 'upload.html', {'form': form})