import logging
import shelve
import typing
from decimal import Decimal
from threading import Thread
from time import sleep

import prometheus_client
import uvicorn
from fastapi import FastAPI
from forex_python.converter import CurrencyRates
from prometheus_client import Gauge
from starlette.responses import JSONResponse, HTMLResponse

from crypto_monitor import DATA_PATH
from crypto_monitor.forex import get_fio_rates
from crypto_monitor.kraken import download_kraken_table
from crypto_monitor.schemas import Account

db = shelve.open(str(DATA_PATH / 'db.shelf'), writeback=True)
if 'accounts' not in db:
    db['accounts'] = {}
    db.sync()

accounts = typing.cast(dict[str, Account], db['accounts'])

app = FastAPI()


@app.post("/{account}/{currency}/balance")
def update_balance(account: str, currency: str, new_balance: str):
    currency = currency.upper()
    if account not in accounts:
        accounts[account] = Account(name=account)

    accounts[account].balances[currency] = Decimal(new_balance)
    db.sync()

    BALANCE_METRIC.labels(account, currency).set(float(new_balance))
    return JSONResponse({"new_balance": new_balance})


@app.get("/{account}/{currency}/balance")
def get_balance(account: str, currency: str):
    currency = currency.upper()

    if account not in accounts:
        return JSONResponse({"error": "Account not found."}, status_code=404)

    return JSONResponse({"balance": str(accounts[account].balances.get(currency, 0))})


@app.get("/metrics")
def get_metrics():
    return HTMLResponse(content=prometheus_client.generate_latest(), status_code=200)


BALANCE_METRIC = Gauge('balance', 'Balance of the given account', ['account', 'currency'])
BALANCE_VALUE_METRIC = Gauge('balance_value', 'Balance value of the given account in CZK', ['account', 'currency'])
FOREX_METRIC = Gauge('forex', 'Forex rate of the given currency', ['from_currency', 'to_currency'])
TICKER_METRIC = Gauge('ticker_czk', 'Ticker of the given currency in CZK', ['currency'])


def _init_balance_metrics():
    for account in list(accounts.values()):
        for currency, amount in list(account.balances.items()):
            BALANCE_METRIC.labels(account.name, currency).set(float(amount))


def _update_metrics():
    while True:
        try:
            # converter = CurrencyRates()

            # eur_to_czk = converter.get_rate('EUR', 'CZK')
            # czk_to_eur = converter.get_rate('CZK', 'EUR')
            rates = get_fio_rates()
            eur_to_czk = rates['EURCZK']
            czk_to_eur = rates['CZKEUR']

            kraken_table = download_kraken_table()

            FOREX_METRIC.labels('EUR', 'CZK').set(float(eur_to_czk))
            FOREX_METRIC.labels('CZK', 'EUR').set(float(czk_to_eur))
            TICKER_METRIC.labels('BTC').set(float(kraken_table['BTC EUR'] * eur_to_czk))

            for account in list(accounts.values()):
                for currency, amount in list(account.balances.items()):
                    amount_in_eur = kraken_table[f"{currency} EUR"] * float(amount)
                    amount_in_czk = amount_in_eur * eur_to_czk

                    BALANCE_VALUE_METRIC.labels(account.name, currency).set(amount_in_czk)

        except Exception:
            logging.exception("Metrics update failed.")

        sleep(10)


if __name__ == '__main__':
    Thread(target=_update_metrics, daemon=True).start()

    _init_balance_metrics()
    uvicorn.run(app, host='0.0.0.0', port=8758)
