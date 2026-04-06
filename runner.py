from oanda_api import OandaAPI

api = OandaAPI()

while True:
    command = input("Enter commnad:")
    if command == "T":
        print("Make a trade")
        trade_id, ok = api.place_trade("USD_MXN", 1000)
        print("Trade Id:", trade_id)
        pass
    if command == "C":
        print("Closing ", trade_id)
        print(api.close_trade(trade_id))
    if command == "Q":
        break