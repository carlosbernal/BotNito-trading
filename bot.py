import os
import pprint
import time
import requests
import pandas as pd
import schedule
import decimal as Decimal
from dotenv import load_dotenv

load_dotenv()

from settings import Settings
from log_wrapper import LogWrapper
from timing import Timing
from oanda_api import OandaAPI
from technicals import Technicals
from trade_manager import TradeManager
from defs import BUY, SELL, NONE
from datetime import datetime, timedelta, timezone, date
from fake_useragent import UserAgent
from sie_banxico import SIEBanxico


GRANULARITY = "M10"
SLEEP = 10.0

class TradingBot():
    def __init__(self):
        self.log = LogWrapper("Bot")
        self.tech_log = LogWrapper("TechnicalsBot")
        self.trade_log = LogWrapper("Trade")
        self.trade_pairs = Settings.get_pairs()
        self.settings = Settings.load_settings()
        self.api = OandaAPI()
        self.trade_manager = TradeManager(self.api, self.settings, self.trade_log)
        self.timings = {p : Timing(self.api.last_complete_candle(p, GRANULARITY)) for p in self.trade_pairs}    
        self.log_message(f"Bot started with\n {pprint.pformat(self.settings)}")
        self.log_message(f"Bot Timings\n {pprint.pformat(self.timings)}")
        #self.saveTodaysIndicators()

    def log_message(self, msg):
        self.log.logger.debug(msg)

    def update_timings(self):
        for pair in self.trade_pairs:
            current = self.api.last_complete_candle(pair, GRANULARITY)
            self.timings[pair].ready = False
            if current > self.timings[pair].last_candle:
                self.timings[pair].ready = True
                self.timings[pair].last_candle = current
                self.log_message(f"{pair} new candle {current}")

    def process_pairs(self):
        trades_to_make = []
        for pair in self.trade_pairs:
            if self.timings[pair].ready == True:
                self.log_message(f"Ready to trade {pair}")
                techs = Technicals(self.settings[pair], self.api, pair, GRANULARITY, log = self.tech_log)
                decision = techs.get_trade_decision(self.timings[pair].last_candle)
                if decision is not None:
                    units = decision * self.settings[pair].units
                else:
                    print("Decision is None")
                # within this function we need to check for open trades for the pairs we want to trade
                # and close them before creating a new pair for said pair
                if units != 0:
                    trades_to_make.append({'pair': pair, 'units': units})                    
                    self.log_message(f"We would have traded {units} units")
        if len(trades_to_make) > 0:   
            print("Time to call the trade manager...")         
            self.trade_manager.place_trades(trades_to_make)


    def run(self):
        self.saveTodaysIndicators()

        while True:
            self.update_timings()
            self.process_pairs()
            time.sleep(SLEEP)

    # this function will run on script's load everyday once, to prevent multiple api calls during the same day
    def saveTodaysIndicators(self):
        # Fed's Interest rate
        av_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        url = f'https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=monthly&apikey={av_key}'
        r = requests.get(url)
        data = r.json()

        df = pd.json_normalize(data['data'])
        df['date'] = pd.to_datetime(df['date'])    
        df.set_index('date', inplace=True)   

        IR_Fed = float(df.iloc[0, 0])
        # CNNs FNG
        CNN_BASE_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
        dia = date.today()
        diaStr = dia.strftime('%Y-%m-%d')

        ua = UserAgent()
        headers = {'User-Agent': ua.random,}
        r = requests.get(CNN_BASE_URL+ diaStr, headers=headers)

        data = r.json()
        df = pd.json_normalize(data['fear_and_greed_historical']['data'])

        d = []
        for data in ((data['fear_and_greed_historical']['data'])):
                x = int(data['x'])
                x = datetime.fromtimestamp(x/1000).strftime('%Y-%m-%d')
                y = int(data['y'])           
                                
                d.append({'Date': x, 'FNG': y,'Rating':  data['rating']})
                
        df = pd.DataFrame(d)

        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        FNG = int(df.iloc[0, 0])

        tokenBanxico = os.getenv("BANXICO_TOKEN")
        serieBanxico = "SF61745"

        api = SIEBanxico(token = tokenBanxico, id_series = [serieBanxico], language = 'en')
        data = api.get_timeseries_range(init_date=diaStr, end_date=diaStr)
        df = pd.DataFrame(data['bmx']['series'][0]['datos']) 

        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)    
        df.set_index('fecha', inplace=True)

        #df = pd.read_pickle("Banxico.pkl") 
        IR_Banxico = float(df.iloc[0, 0])

        # initialize list of lists
        data = [[dia, IR_Fed, IR_Banxico, FNG]]

        # Create the pandas DataFrame
        df = pd.DataFrame(data, columns=['Date','IR_Fed', 'IR_Banxico','FNG'])

        df.to_pickle(diaStr+".pkl")

        self.log_message(f"Indicators retrieved and save at:  {diaStr}.pkl")


if __name__ == "__main__":
    b = TradingBot()
    b.run()