import re
from copy import deepcopy
from time import time

import requests

RATE_REFRESH_RATE_SECONDS = 3600

_last_update_timestamp = 0
_rate_cache = None


def get_fio_rates():
    global _last_update_timestamp, _rate_cache
    current_timestamp = time()

    if current_timestamp - _last_update_timestamp > RATE_REFRESH_RATE_SECONDS:
        _rate_cache = _download_fio_rates()
        _last_update_timestamp = current_timestamp

    return deepcopy(_rate_cache)


def _download_fio_rates():
    url = "https://www.fio.cz/stocks-investments/other-fio-services/foreign-exchange"
    response = requests.get(url)
    response.raise_for_status()

    eur_pattern = r'<tr><td class="tleft"><strong>EUR<\/strong><\/td><td class="tright">([\d,]+)<\/td><td class="tright">([\d,]+)<\/td><\/tr>'
    match = re.search(eur_pattern, response.text)
    if not match:
        raise ValueError("EUR rate not found")

    sell_rate = match.group(1)
    buy_rate = match.group(2)

    sell_rate = _rate_to_float(sell_rate)
    buy_rate = 1 / _rate_to_float(buy_rate)

    return {
        'EURCZK': sell_rate,
        'CZKEUR': buy_rate,
    }


def _rate_to_float(value):
    return float(value.replace(',', '.'))
