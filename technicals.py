import os
import pandas as pd
import datetime
import requests
from dotenv import load_dotenv
from fake_useragent import UserAgent
from sie_banxico import SIEBanxico
from datetime import datetime, timedelta, timezone, date
import neat
import pickle

load_dotenv()
import yfinance as yf
import emailer

""" VARIABLES SECTION """
STOP_LOSS_LIMIT = 90
TP_STEP = 0.1
SL_REDUCER = 0.1
CNN_BASE_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"


from defs import BUY, SELL, NONE

class Technicals():
    def __init__(self, settings, api, pair, granularity, log=None):
        self.settings = settings
        self.log = log
        self.api = api
        self.pair = pair
        self.granulatiry = granularity

    def log_message(self, msg):
        if self.log is not None:
            self.log.logger.debug(msg)

    def fetch_candles(self, row_count, candle_time):
        status_code, df = self.api.fetch_candles(self.pair, count=row_count, granularity=self.granulatiry)

        if df is None:
            self.log_message(f"Error fetching candles for pair: {self.pair} {candle_time}, df None")
            return None
        elif df.iloc[-1].time != candle_time:
            self.log_message(f"Error fetching candles for pair: {self.pair} {candle_time} vs {df.iloc[-1].time} ")
            return None
        else:
            return df

    def process_candles(self, df):
        ## Calculating Technical Indicators
        df.reset_index(drop=True, inplace=True)
        df['PAIR'] = self.pair
        df['SPREAD'] = df.ask_c - df.bid_c
        short_prev = 'PREV_SHORT'
        long_prev = 'PREV_LONG'
        short_col = f"MA_{self.settings.short_ma}"
        long_col = f"MA_{self.settings.long_ma}"
        df[short_col] = df.mid_c.rolling(window=self.settings.short_ma).mean()
        df[long_col] = df.mid_c.rolling(window=self.settings.long_ma).mean()
        df[short_prev] = df[short_col].shift(1)
        df[long_prev] = df[long_col].shift(1)
        df['D_PREV'] = df[short_prev] - df[long_prev]
        df['D_NOW'] = df[short_col] - df[long_col]

        last = df.iloc[-1]
        decision = NONE

        #Taking a decision
        """ if last.D_NOW < 0 and last.D_PREV > 0:
            decision = SELL
        elif last.D_NOW > 0 and last.D_PREV <0:
            decision = BUY """

        log_cols = ['time','volume','mid_o','mid_h', 'mid_l','mid_c','SPREAD','PAIR', short_col, long_col, short_prev, long_prev, 'D_PREV', 'D_NOW']
        #previous_closing = df.iloc[-2].mid_c

        decision = get_Trade_Action(df.iloc[-1].volume, df.iloc[-1].mid_o, df.iloc[-1].mid_h, df.iloc[-1].mid_l, df.iloc[-1].mid_c)

        self.log_message(f"To be process by NN:  \n {df.iloc[-1].volume}, {df.iloc[-1].mid_o}, {df.iloc[-1].mid_h}, {df.iloc[-1].mid_l}, {df.iloc[-1].mid_c}")
        self.log_message(f"Processed Data:  \n {df[log_cols].tail(2)}")
        self.log_message(f"Trade_decision: {decision}")
        return decision        

    def get_trade_decision(self, candle_time):        
        max_rows = self.settings.long_ma + 2
        self.log_message(f"get_trade_decision() pair: {self.pair} max_rows: {max_rows}")

        df = self.fetch_candles(max_rows, candle_time)

        if df is not None:
            return self.process_candles(df)        
        return None
    

def get_Trade_Action(volume, mid_o, mid_h, mid_l, mid_c):
    dia = date.today()
    diaStr = dia.strftime('%Y-%m-%d')

    indicators_df = pd.read_pickle(diaStr+".pkl")

    FnG = getCurrFNG()           
    IR_Fed = indicators_df['IR_Fed'][0]
    IR_Banxico = indicators_df['IR_Banxico'][0]
    Vix = getVIX()
    
    # Unpickle saved winner
    with open("winner-experiment-20-F.pkl", "rb") as f:
        winner38d = pickle.load(f)
    # Unpickle saved winner
    #with open("winner-experiment-20-G.pkl", "rb") as f:
     #   winnerG = pickle.load(f)

    # Unpickle saved winner
    #with open("winner-experiment-20-H.pkl", "rb") as f:
     #   winnerH = pickle.load(f)

    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-experiment-38d.txt')

    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                        config_path)

    # Convert loaded genome into required data structure
    gen = [(1, winner38d)]

    #gen.fitness = 0  # start with fitness level of 0
    net38d = neat.nn.FeedForwardNetwork.create(winner38d, config)
    #netG = neat.nn.FeedForwardNetwork.create(winnerG, config)
    #netH = neat.nn.FeedForwardNetwork.create(winnerH, config)

    print(f"Values before NN: {volume}, {mid_o}, {mid_h}, {mid_l}, {mid_c}, {IR_Banxico}, {IR_Fed}, {FnG}, {Vix}")
    
    output38d = net38d.activate((volume, mid_o, mid_h, mid_l, mid_c, IR_Banxico, IR_Fed, FnG, Vix)) 
    #outputG = netG.activate((previous_c, volume, mid_o, mid_h, mid_l, mid_c, IR_Banxico, IR_Fed, FnG)) 
    #outputH = netH.activate((previous_c, volume, mid_o, mid_h, mid_l, mid_c, IR_Banxico, IR_Fed, FnG)) 

    #print(f"Outputs, F: {outputF[0]}, G: {outputG[0]}, H: {outputH[0]}")
    if (output38d[0] > 0.5):
        print(f"its a LONG, 38d: {output38d[0]}")
        return BUY
    elif (output38d[0] < -0.5):
        print(f"its a SHORT, 38d: {output38d[0]}")
        return SELL

    """ if (outputF[0] > 0.5 and outputG[0] > 0.5) or (outputG[0] > 0.5 and outputH[0] > 0.5) or (outputF[0] > 0.5 and outputH[0] > 0.5):
        print(f"its a LONG, F: {outputF[0]}, G: {outputG[0]}, H: {outputH[0]}")
        return BUY
    elif (outputF[0] < 0.5 and outputG[0] < 0.5) or (outputG[0] < 0.5 and outputH[0] < 0.5) or (outputF[0] < 0.5 and outputH[0] < 0.5) :
        print(f"its a SHORT, F: {outputF[0]}, G: {outputG[0]}, H: {outputH[0]}")
        return SELL """         
    
#TODO: Change this function to retrieve only todays data And add functionality that handles no DATA or Connection loss
def getIRFromBanxico():
    """ We can get all dates from banxico in one call and then save the df and find the required date as
    need it
    """
    tokenBanxico = os.getenv("BANXICO_TOKEN")
    serieBanxico = "SF61745"
    dia = date.today()
    new_date = datetime(dia.year, dia.month, dia.day)
    diaStr = dia.strftime('%Y-%m-%d')
    
    
    api = SIEBanxico(token = tokenBanxico, id_series = [serieBanxico], language = 'en')
    data = api.get_timeseries_range(init_date=diaStr, end_date=diaStr)
    df = pd.DataFrame(data['bmx']['series'][0]['datos']) 

    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)    
    df.set_index('fecha', inplace=True)

    #df = pd.read_pickle("Banxico.pkl") 
    IR_Banxico = float(df.iloc[0, 0])

    return IR_Banxico
        
def getIRFed():
    av_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    url = f'https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=monthly&apikey={av_key}'
    r = requests.get(url)
    data = r.json()
    
    df = pd.json_normalize(data['data'])

    #df = pd.read_pickle("AlphaAvantageFedData.pkl") 

    df['date'] = pd.to_datetime(df['date'])    
    df.set_index('date', inplace=True)           
    
    IR_Fed = float(df.iloc[0, 0])
    
    return IR_Fed
    
def getCurrFNG():
    ua = UserAgent()
    headers = {'User-Agent': ua.random,}    
    r = requests.get(CNN_BASE_URL, headers=headers)
    data = r.json()

    return int(data['fear_and_greed']['score'])

def getFNGday():
    CNN_BASE_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
    dia = date.today()
    new_date = datetime(dia.year, dia.month, dia.day)
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
                        
            d.append(
            {
                'Date': x,
                'FNG': y,
                'Rating':  data['rating']
            }
            )
    df = pd.DataFrame(d)
    
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    FNG = int(df.iloc[0, 0])

    return FNG

def getVIX():
    VIX = None
    
    vix = yf.download('^VIX', period='1d', interval='1m')
    vix = vix[['Adj Close']]

    #vix.rename(columns={'Adj Close': 'VIX'}, inplace=True)

    VIX =vix['Adj Close'].iloc[-1]
    
    if VIX is not None:
        return VIX
    else:
        emailer.sendEmail("I was not able to retrieve VIX, technicals.py ln; 245")
        