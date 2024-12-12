from django.http import JsonResponse
from .calculateFiles.bonbast import get_prices_from_api
from .calculateFiles.token_manager import TokenManager
from django.core.cache import cache
from .bonbast.server import get_history
from .bonbast.helpers.utils import filter_valids, convert_json
from datetime import datetime, timedelta
import json
from collections import OrderedDict

def convert_to_date(date_str):
    dt = datetime.strptime(date_str, "%B %d, %Y %H:%M")
    yesterday = dt - timedelta(days=1)
    return datetime(yesterday.year, yesterday.month, yesterday.day)

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



def currency_price(request):
    cache_timeout = 10

    currency_price_cache = cache.get('currency_price')

    if currency_price_cache is None:
        token_manager = TokenManager()
        token = token_manager.generate()
        current_prices = get_prices_from_api(token.value) #important

        specific_date = convert_to_date(current_prices['last_modified'])
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
        sorted_final_json["shirini"] = False
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

