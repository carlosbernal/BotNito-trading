import os
from dotenv import load_dotenv

load_dotenv()

# Live account
API_KEY = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
OANDA_URL = os.getenv("OANDA_URL", "https://api-fxtrade.oanda.com/v3")

# Practice / demo account
API_KEY_DEMO = os.getenv("OANDA_API_KEY_DEMO")
ACCOUNT_ID_DEMO = os.getenv("OANDA_ACCOUNT_ID_DEMO")
OANDA_URL_DEMO = os.getenv("OANDA_URL_DEMO", "https://api-fxpractice.oanda.com/v3")

SECURE_HEADER = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

BUY = 1
SELL = -1
NONE = 0
