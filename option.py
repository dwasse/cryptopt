import datetime
import math
import pytz
from scipy.stats import norm


day = 86400


class Option:
    def __init__(self,
                 underlying_pair,
                 option_type,
                 strike,
                 expiry,
                 interest_rate=0,
                 volatility=None,
                 underlying_price=None,
                 now=datetime.datetime.now(),
                 exchange_symbol=None):
        self.underlying_pair = underlying_pair
        if not option_type == 'call' and not option_type == 'put':
            raise ValueError('Expected "call" or "put", got ' + option_type)
        self.option_type = option_type
        self.strike = strike
        self.expiry = expiry
        self.interest_rate = interest_rate
        if volatility is not None:
            self.volatility = volatility        # decimal
        self.underlying_price = underlying_price
        self.now = now
        self.exchange_symbol = exchange_symbol
        self.time_left = self.get_time_left(self.now)
        self.d1 = None
        self.d2 = None
        self.theo = None
        self.delta = None
        self.gamma = None
        self.theta = None
        self.present_value = None

    def __str__(self):
        return self.underlying_pair + " " + str(self.strike) + " " + self.option_type + " with expiry " + str(self.expiry)

    def get_time_left(self, current_datetime=datetime.datetime.now()):
        return (self.expiry - current_datetime).total_seconds() / (day * 365)

    def update_underlying_price(self, underlying_price):
        self.underlying_price = underlying_price

    def update_now(self, new_time):
        self.now = new_time

    def calc_greeks(self, verbose=False):
        self.calc_theo()
        self.calc_delta()
        self.calc_gamma()
        self.calc_theta()
        if verbose:
            print("Calculated greeks for " + str(self) + ": delta=" + str(self.delta) + ", gamma=" + str(self.gamma)
                  + ", theta=" + str(self.theta))

    def calc_theo(self, time_left=None, store=True):
        if not time_left:
            time_left = self.time_left
        d1 = (math.log(self.underlying_price / self.strike) + (self.interest_rate + ((self.volatility ** 2) / 2.0))
              * time_left) / (self.volatility * math.sqrt(time_left))
        d2 = d1 - (self.volatility * math.sqrt(time_left))
        present_value = self.strike * math.exp(-self.interest_rate * time_left)
        theo = None
        if self.option_type == "call":
            theo = max((self.underlying_price * norm.cdf(d1)) - (present_value * norm.cdf(d2)), 0)
        elif self.option_type == "put":
            theo = max((norm.cdf(-d2) * present_value) - (norm.cdf(-d1) * self.underlying_price), 0)
        if store:
            self.d1 = d1
            self.d2 = d2
            self.theo = theo
            self.present_value = present_value
        return theo

    def calc_delta(self, underlying_price=None, store=True):
        if underlying_price:
            d1 = (math.log(underlying_price / self.strike) + (self.interest_rate + ((self.volatility ** 2) / 2.0))
                  * self.time_left) / (self.volatility * math.sqrt(self.time_left))
        else:
            d1 = self.d1
        delta = None
        if self.option_type == 'call':
            delta = norm.cdf(d1)
        elif self.option_type == 'put':
            delta = -norm.cdf(-d1)
        if store:
            self.delta = delta
        return delta

    def calc_gamma(self, underlying_pct_change=.1):
        original_delta = self.calc_delta()
        underlying_change = self.underlying_price * (underlying_pct_change / 100)
        incremented_price = self.underlying_price + underlying_change
        incremented_delta = self.calc_delta(underlying_price=incremented_price, store=False)
        self.gamma = (incremented_delta - original_delta) / underlying_change
        return self.gamma

    def calc_theta(self, time_change=1/365):
        if time_change >= self.time_left:
            time_change = self.time_left / 2
        original_theo = self.calc_theo()
        advanced_time = self.time_left - time_change
        advanced_theo = self.calc_theo(time_left=advanced_time)
        self.theta = -1 * (advanced_theo - original_theo)
        return self.theta
