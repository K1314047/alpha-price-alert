import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


API_URL = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.json")
last_alerts = {}


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    if config.get("threshold_percent", 0) <= 0:
        raise ValueError("threshold_percent must be greater than 0")
    if not config.get("symbols"):
        raise ValueError("symbols must contain at least one symbol")
    return config


def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        print("Telegram error:", error, flush=True)


def get_alpha_data():
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", []) if payload.get("success") else []
    except (requests.RequestException, ValueError) as error:
        print("Binance API error:", error, flush=True)
        return []


def find_symbol(data, symbol):
    symbol = symbol.upper()
    return next((item for item in data if item.get("symbol", "").upper() == symbol), None)


def calc_change(base, current):
    return ((current - base) / base) * 100


def get_now(timezone_name):
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except Exception as error:
        raise ValueError(f"Invalid timezone: {timezone_name}") from error


def main():
    print("Alpha Price Alert started", flush=True)
    base_prices = {}
    base_date = None

    while True:
        try:
            config = load_config()
            symbols = [symbol.upper() for symbol in config["symbols"]]
            threshold = config["threshold_percent"]
            interval = config.get("check_interval", 10)
            telegram = config["telegram"]
            now = get_now(config.get("timezone", "Asia/Shanghai"))
            today = now.date()

            # Each new calendar day starts from the first successfully fetched price.
            if base_date != today:
                base_prices.clear()
                last_alerts.clear()
                base_date = today
                print(f"Daily price baseline reset: {today} ({now.tzname()})", flush=True)

            configured_symbols = set(symbols)
            active_base_prices = {
                symbol: price for symbol, price in base_prices.items()
                if symbol in configured_symbols
            }
            base_prices.clear()
            base_prices.update(active_base_prices)
            active_alerts = {
                key: alerted for key, alerted in last_alerts.items()
                if key[0] in configured_symbols
            }
            last_alerts.clear()
            last_alerts.update(active_alerts)
            alpha_data = get_alpha_data()

            for symbol in symbols:
                item = find_symbol(alpha_data, symbol)
                if not item:
                    print(f"{symbol} not found", flush=True)
                    continue

                try:
                    current_price = float(item["price"])
                except (KeyError, TypeError, ValueError):
                    continue

                if symbol not in base_prices:
                    base_prices[symbol] = current_price
                    print(f"Base price set {symbol}: {current_price}", flush=True)
                    continue

                base_price = base_prices[symbol]
                change = calc_change(base_price, current_price)
                level = int(abs(change) // threshold)
                direction = "UP" if change > 0 else "DOWN"
                alert_key = (symbol, direction, level)

                if abs(change) >= threshold and not last_alerts.get(alert_key):
                    last_alerts[alert_key] = True
                    message = (
                        "🚨 <b>Alpha Alert</b>\n\n"
                        f"💎 Symbol: <b>{symbol}</b>\n\n"
                        f"💰 Current: {current_price}\n\n"
                        f"📊 Base: {base_price}\n\n"
                        f"📈 Change: {change:.2f}%\n\n"
                        f"🕒 Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                    )
                    print(message, flush=True)
                    send_telegram(telegram["bot_token"], telegram["chat_id"], message)

            time.sleep(interval)
        except Exception as error:
            print("Main error:", error, flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
