import requests

BASE_URL = 'https://bonbast.com'
USER_AGENT = ('Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/120.0.0.0 Mobile Safari/537.36')

def get_prices_from_api(token: str):
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
        'authority': 'bonbast.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en-GB;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://bonbast.com',
        'referer': 'https://bonbast.com/',
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
    
    return r



class ResetAPIError(Exception):
    """
    Exception raised when the API token is expired and a new token is required.
    """
    pass

