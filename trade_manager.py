import pandas as pd
from defs import BUY, SELL, NONE
from datetime import date

class TradeManager():
    curr_position = None
    curr_tradeId = 0

    def __init__(self, api, settings, log=None):
        self.api = api
        self.log = log
        self.settings = settings         

    def log_message(self, msg):
        if self.log is not None:
            self.log.logger.debug(msg)

    #make sure the trades are closed correctly
    def close_trades(self, pairs_to_close):

        open_trades, ok = self.api.open_trades()

        if len(open_trades) > 1:
            self.log_message("***** More than on trade OPEN !! ****")

        if ok == False: # *** Very important     ****
            self.log_message("***** Error fetching the open trades!! ****")

        ids_to_close = [x.trade_id for x in open_trades if x.instrument in pairs_to_close]

        self.log_message(f"TradeManager: close_trades() pairs_to_close: {pairs_to_close}")
        self.log_message(f"TradeManager: close_trades() open_trades: {open_trades}")
        self.log_message(f"TradeManager: close_trades() ids_to_close: {ids_to_close}")

        for t in ids_to_close:
            ok = self.api.close_trade(t)
            if ok == False:
                self.log_message(f"TradeManager: close_trades() {t} FAILED TO CLOSE ")
            else:
                self.log_message(f"TradeManager: close_trades() {t} Closed ")

    def create_trades(self, trades_to_make):
        for t in trades_to_make:
            trade_id = self.api.place_trade(t['pair'], t['units'])
            if trade_id is not None:
                self.log_message(f"TradeManager:Opened {trade_id} {t}")
                
                #save new trade id and position
                self.curr_tradeId = trade_id
                if t['units'] > 0:
                    self.curr_position = BUY
                elif t['units'] < 0:
                    self.curr_position = SELL
                elif t['units'] == 0:
                    self.curr_position = NONE

            else:
                self.log_message(f"TradeManager:FAILED TO OPEN {t}")

    def place_trades(self, trades_to_make):
        self.log_message(f"TradeManager:places_trades() {trades_to_make}")

        if len(trades_to_make) > 1:
            self.log_message(f"TradeManager:More than one trade detected {trades_to_make}")
        elif len(trades_to_make) ==0:
            self.log_message(f"TradeManager:trades to make is EMPTY {trades_to_make}")
        elif len(trades_to_make) ==1:

            if (trades_to_make[0]['units'] > 0 and self.curr_position == BUY) or (trades_to_make[0]['units'] < 0 and self.curr_position == SELL): 
                # DO NOTHING
                self.log_message(f"TradeManager:Trying to open a trade on my curent position, do NOTHING {trades_to_make}")
            else: #CONTINUE
                pairs = [x['pair'] for x in trades_to_make]
                self.close_trades(pairs)
                self.create_trades(trades_to_make)

    


                

            




        