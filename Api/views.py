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
            print('*', currency_code)
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

def currency_price(request):
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

        sorted_final_json = convert_currency_data(sorted_final_json)
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

