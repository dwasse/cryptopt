import datetime
from option import Option


class TheoEngine:
    def __init__(self, underlying_pair, underlying_price, strikes, expirations, atm_volatility, interest_rate=0):
        self.underlying_pair = underlying_pair
        self.underlying_price = underlying_price
        self.strikes = strikes
        self.expirations = expirations
        self.atm_volatility = atm_volatility
        self.interest_rate = interest_rate
        self.now = datetime.datetime.now()
        self.options = {
            'call': {},
            'put': {}
        }

        for expiry in self.expirations:
            for call_put in ['call', 'put']:
                self.options[call_put][expiry] = {}
            for strike in self.strikes:
                for call_put in ['call', 'put']:
                    option = Option(
                        underlying_pair=self.underlying_pair,
                        underlying_price=self.underlying_price,
                        call_put=call_put,
                        strike=strike,
                        volatility=self.atm_volatility,
                        interest_rate=self.interest_rate,
                        expiry=expiry,
                        now=self.now
                    )
                    option.calc_greeks(verbose=True)
                    self.options[call_put][expiry][strike] = option

    def update_underlying_price(self, underlying_price):
        self.underlying_price = underlying_price
        for call_put in self.options:
            for expiry in self.options[call_put]:
                for strike in self.options[call_put][expiry]:
                    option = self.options[call_put][expiry][strike]
                    option.update_underlying_price(self.underlying_price)
                    option.calc_greeks()
