from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import logging
import requests
import time

class BitcoinPlus(plugins.Plugin):
    __author__ = 'OrangeGlowInc with Plugin Master'
    __version__ = '0.1.0'
    __license__ = 'MIT'
    __description__ = 'Displays the price of bitcoin or any crypto in any national currency. Position + abbreviation support.'
    __name__ = 'bitcoinplus'
    __help__ = """
    Example toml:
    main.plugins.bitcoinplus.enabled = true
    main.plugins.bitcoinplus.coin = "ethereum"			# Any crypto: bitcoin, ethereum, litecoin, dogecoin, etc.
    main.plugins.bitcoinplus.currency = "gbp"			# Any fiat: usd, cny, eur, gbp, zar, brl, etc.
    main.plugins.bitcoinplus.api_url = "https://api.coingecko.com/api/v3/simple/price"
    main.plugins.bitcoinplus.refresh_interval = 300		# in seconds (5 minutes)
    main.plugins.bitcoinplus.position.x = 206			# screen X position
    main.plugins.bitcoinplus.position.y = 195			# screen Y position
    """
    __dependencies__ = {'pip': ['requests']}

    _last_price = '...'
    _has_internet = False
    _last_fetch_time = 0

    _currency_symbols = {
        'usd': '$', 'eur': '€', 'gbp': '£', 'jpy': '¥', 'inr': '₹',
        'aud': 'A$', 'cad': 'C$', 'chf': 'CHF', 'cny': '¥', 'rub': '₽',
        'krw': '₩', 'try': '₺'
    }

    def on_loaded(self):
        logging.info("[bitcoinplus] plugin loaded")

    def _get_symbol(self, currency_code):
        return self._currency_symbols.get(currency_code.lower(), currency_code.upper())

    def _get_abbreviation(self, name):
        return {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "dogecoin": "DOGE",
            "litecoin": "LTC",
            "monero": "XMR"
        }.get(name.lower(), name.upper()[:4])

    def _fetch_price(self):
        coin = self.options.get("coin", "bitcoin").lower()
        currency = self.options.get("currency", "usd").lower()
        api_url = self.options.get("api_url", "https://api.coingecko.com/api/v3/simple/price")

        try:
            logging.debug(f"[bitcoinplus] Fetching price for {coin}/{currency}")
            response = requests.get(api_url, params={"ids": coin, "vs_currencies": currency}, timeout=10)
            response.raise_for_status()
            data = response.json()
            return f"{data[coin][currency]:,.2f}"
        except Exception as e:
            logging.error(f"[bitcoinplus] Failed to fetch {coin}/{currency} price: {e}")
            return "---"

    def on_ui_setup(self, ui):
        if ui.is_waveshare_v4():
            pos = (123, 110)
        elif ui.is_waveshare_v1():
            pos = (170, 80)
        elif ui.is_waveshare144lcd():
            pos = (53, 77)
        elif ui.is_inky():
            pos = (140, 68)
        elif ui.is_waveshare27inch():
            pos = (192, 138)
        else:
            pos = (206, 195)

        ui.add_element('bitcoinplus', LabeledValue(
            color=BLACK,
            label='',
            value='Loading...',
            position=pos,
            label_font=fonts.Small,
            text_font=fonts.Small
        ))

    def on_ui_update(self, ui):
        coin = self.options.get("coin", "bitcoin").lower()
        currency = self.options.get("currency", "usd").lower()
        symbol = self._get_symbol(currency)
        refresh_interval = int(self.options.get("refresh_interval", 900))
        current_time = time.time()

        if current_time - self._last_fetch_time >= refresh_interval:
            price = self._fetch_price()
            abbr = self._get_abbreviation(coin)
            self._last_price = f"{abbr}/{currency.upper()}: {symbol}{price}"
            self._last_fetch_time = current_time

        ui.set("bitcoinplus", self._last_price)

    def on_internet_available(self, ui):
        self._has_internet = True
        logging.debug("[bitcoinplus] Internet is available")

    def on_sleep(self):
        if self._has_internet:
            coin = self.options.get("coin", "bitcoin").lower()
            currency = self.options.get("currency", "usd").lower()
            symbol = self._get_symbol(currency)
            abbr = self._get_abbreviation(coin)
            price = self._fetch_price()
            self._last_price = f"{abbr}/{currency.upper()}:\n{symbol}{price}"

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element("bitcoinplus")