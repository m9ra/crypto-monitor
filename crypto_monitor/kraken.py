import requests


def download_kraken_table():
    url = "https://api.kraken.com/0/public/Ticker?pair=XBTEUR"
    response = requests.get(url)
    data = response.json()

    return {
        'BTC EUR': float(data['result']['XXBTZEUR']['b'][0]),
        'EUR BTC': 1 / float(data['result']['XXBTZEUR']['a'][0]),
    }
