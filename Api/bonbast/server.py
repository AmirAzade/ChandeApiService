import re
from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict

import requests
from bs4 import BeautifulSoup

try:
    from .models import *
except ImportError:
    from models import *

BASE_URL = 'https://'
USER_AGENT = ('Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/120.0.0.0 Mobile Safari/537.36')
SELL = '1'
BUY = '2'


def int_try_parse(value) -> Optional[int]:
    """
    Attempts to convert a string value to an integer, returning None if conversion fails or results in 0.
    
    :param value: The string value to convert.
    :return: The converted integer or None.
    """
    try:
        parsed = int(value)
        return None if parsed == 0 else parsed
    except ValueError:
        return None


def get_token_from_main_page():
    """
    Retrieves a token from the main page of bon-bast.com.
    
    :return: The retrieved token.
    :raises SystemExit: If an HTTP error occurs or the token is not found.
    """
    cookies = {
        'cookieconsent_status': 'true',
        'st_bb': '0',
    }
    headers = {
        'authority': 'bon-bast.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en-GB;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://bon-bast.com/',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': USER_AGENT,
    }

    try:
        r = requests.get(BASE_URL, headers=headers, cookies=cookies)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    except requests.exceptions.ConnectionError:
        raise SystemExit('Error: Failed to connect to bonbast')

    search = re.search(r"param\s*[=:]\s*\"(.+)\"", r.text, re.MULTILINE)
    if search is None or search.group(1) is None:
        raise SystemExit('Error: token not found in the main page')

    return search.group(1)


def get_prices_from_api(token: str) -> Tuple[List[Currency], List[Coin], List[Gold]]:
    """
    Retrieves currency, coin, and gold prices from the bonbast API using a provided token.
    
    :param token: The token to use for the API request.
    :return: A tuple containing lists of Currency, Coin, and Gold objects.
    :raises SystemExit: If an HTTP error occurs or the API indicates the token is expired.
    """
    cookies = {
        'cookieconsent_status': 'true',
        'st_bb': '0',
    }
    headers = {
        'authority': 'bon-bast.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en-GB;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://bon-bast.com',
        'referer': 'https://bon-bast.com/',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': USER_AGENT,
        'x-requested-with': 'XMLHttpRequest',
    }

    try:
        r = requests.post(f'{BASE_URL}/json', headers=headers, cookies=cookies,
                          data='param=' + token.replace(',', '%2C'))
        r.raise_for_status()
        r = r.json()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    except requests.exceptions.ConnectionError:
        raise SystemExit('Error: Failed to connect to bonbast')

    if 'reset' in r:
        raise ResetAPIError('Error: token is expired')

    currencies: List[Currency] = []
    coins: List[Coin] = []
    golds: List[Gold] = []

    for currency in Currency.VALUES:
        if f'{currency}{BUY}' in r and f'{currency}{SELL}' in r:
            currencies.append(Currency(
                currency.upper(),
                Currency.VALUES[currency],
                sell=int(r[f'{currency}{SELL}']),
                buy=int(r[f'{currency}{BUY}']),
            ))

    for coin in Coin.VALUES:
        if f'{coin}' in r and f'{coin}{BUY}' in r:
            coins.append(Coin(
                coin,
                Coin.VALUES[coin],
                sell=int(r[coin]),
                buy=int(r[f'{coin}{BUY}']),
            ))

    for gold in Gold.VALUES:
        if f'{gold}' in r:
            golds.append(Gold(
                gold,
                Gold.VALUES[gold],
                price=float(r[gold])
            ))

    return currencies, coins, golds


def get_graph_data(
        currency: str,
        start_date: datetime = datetime.today() - timedelta(days=30),
        end_date: datetime = datetime.today(),
) -> Dict[datetime, int]:
    """
    Retrieves historical price data from bon-bast.com/graph for a specified currency within a date range.
    
    :param currency: The currency code.
    :param start_date: The start date of the range.
    :param end_date: The end date of the range.
    :return: A dictionary mapping dates to prices.
    :raises SystemExit: If an HTTP error occurs.
    """
    headers = {
        'authority': 'bon-bast.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,fa;q=0.8',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': 'st_bb=0',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': USER_AGENT,
    }

    try:
        request = requests.post(f'{BASE_URL}/graph', headers=headers, data={
            'currency': currency,
            'stdate': start_date.date(),
            'endate': end_date.date(),
        })
        request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    soup = BeautifulSoup(request.text, 'html.parser')
    for data in soup.find_all("script"):
        # get variables from script and convert them to list
        if "data: {" in data.text:
            price_list = data.text.split("data: [")[1].split("]")[0].split(",")
            date_list = data.text.split("labels: [")[1].split("]")[0].split(',')

            if len(price_list) != len(date_list):
                raise SystemExit('Error: data inconsistency')

            dic = {}
            for i in range(len(price_list)):
                price = int(price_list[i])
                date = re.search(r'\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])', date_list[i]).group(0)
                dic[datetime.strptime(date, "%Y-%m-%d")] = price

            return dic


def get_history(date: datetime = datetime.today() - timedelta(days=1)) -> Tuple[List[Currency], List[Coin]]:
    """
    Retrieves historical currency and coin prices for a specified date.
    
    :param date: The date for which to retrieve prices.
    :return: A tuple containing lists of Currency and Coin objects.
    :raises SystemExit: If the date is out of the valid range or an HTTP error occurs.
    """
    if date.date() < datetime(2012, 10, 9).date():
        raise SystemExit('Error: date is too far in the past. Date must be greater than 2012-10-09')

    if date.date() >= datetime.today().date():
        raise SystemExit(f'Error: date must be less than today({date.today().date()}).')

    headers = {
        'authority': '',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9,fa;q=0.8',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': USER_AGENT,
    }

    try:
        request = requests.post(f'{BASE_URL}/archive', headers=headers, data={'date': date.strftime("%Y-%m-%d")})
        request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    soup = BeautifulSoup(request.text, 'html.parser')
    tables = soup.findAll('table')

    # first and second table are currencies
    currencies: List[Currency] = []
    for table in tables[:2]:
        for row in table.findAll('tr')[1:]:
            cells = row.findAll('td')
            currencies.append(Currency(
                cells[0].text.lower(),
                Currency.VALUES[cells[0].text.lower()],
                sell=int_try_parse(cells[2].text),
                buy=int_try_parse(cells[3].text),
            ))

    # last table is coins
    coins: List[Coin] = []
    for table in tables[-1:]:
        for row in table.findAll('tr')[1:]:
            cells = row.findAll('td')
            coins.append(Coin(
                next(key for key, value in Coin.VALUES.items() if value.lower() == cells[0].text.lower()),
                cells[0].text.lower(),
                sell=int_try_parse(cells[1].text),
                buy=int_try_parse(cells[2].text),
            ))

    return currencies, coins


class ResetAPIError(Exception):
    """
    Exception raised when the API token is expired and a new token is required.
    """
    pass
