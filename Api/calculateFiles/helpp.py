import requests
import re
BASE_URL = 'https://bon-bast.com'
USER_AGENT = ('Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/120.0.0.0 Mobile Safari/537.36')

def get_token_from_main_page():
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