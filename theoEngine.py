import datetime
import pytz
from option import Option
from deribitREST import DeribitREST


class TheoEngine:
    def __init__(self, underlying_pair,
                 underlying_price,
                 expirations=[],
                 strikes={},
                 atm_volatility=None,
                 interest_rate=0):
        self.underlying_pair = underlying_pair
        self.underlying_price = underlying_price
        self.expirations = expirations
        self.strikes = {e: strikes for e in self.expirations}
        self.atm_volatility = atm_volatility
        self.interest_rate = interest_rate
        self.now = pytz.timezone('UTC').localize(datetime.datetime.now())
        self.options = {
            'call': {},
            'put': {}
        }
        self.client = None

    def setup_client(self):
        self.client = DeribitREST()

    def build_options(self):
        if self.strikes is not None and self.expirations is not None:
            for expiry in self.expirations:
                for option_type in ['call', 'put']:
                    self.options[option_type][expiry] = {}
                for strike in self.strikes[expiry]:
                    for option_type in ['call', 'put']:
                        option = Option(
                            underlying_pair=self.underlying_pair,
                            option_type=option_type,
                            strike=strike,
                            expiry=expiry,
                            interest_rate=0,
                            volatility=self.atm_volatility,
                            underlying_price=self.underlying_price,
                            now=self.now
                        )
                        option.calc_greeks(verbose=True)
                        self.options[option_type][expiry][strike] = option

    def build_deribit_options(self):
        self.setup_client()
        instruments = self.client.getinstruments()
        options = [i for i in instruments if i['kind'] == 'option']
        for option_info in options:
            option_type = option_info['optionType']
            strike = option_info['strike']
            expiry = pytz.timezone('GMT').localize(
                datetime.datetime.strptime(option_info['expiration'], '%Y-%m-%d %H:%M:%S GMT')
            )
            if expiry not in self.expirations:
                self.expirations.append(expiry)
            if expiry not in self.strikes:
                self.strikes[expiry] = []
            if strike not in self.strikes[expiry]:
                self.strikes[expiry].append(strike)
            option = Option(
                underlying_pair=self.underlying_pair,
                option_type=option_type,
                strike=strike,
                expiry=expiry,
                interest_rate=0,
                volatility=self.atm_volatility,
                underlying_price=self.underlying_price,
                now=self.now,
                exchange_symbol=option_info['instrumentName']
            )
            print("Time left: " + str(option.time_left))
            option.calc_greeks(verbose=True)
            if expiry in self.options[option_type]:
                self.options[option_type][expiry][strike] = option
            else:
                self.options[option_type][expiry] = {strike: option}

    def update_underlying_price(self, underlying_price):
        self.underlying_price = underlying_price
        for option_type in self.options:
            for expiry in self.options[option_type]:
                for strike in self.options[option_type][expiry]:
                    option = self.options[option_type][expiry][strike]
                    option.update_underlying_price(self.underlying_price)
                    option.calc_greeks()

