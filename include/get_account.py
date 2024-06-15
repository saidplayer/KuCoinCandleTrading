import requests, json, time, datetime
import base64, hashlib, hmac, os
from dotenv import load_dotenv


load_dotenv()
global api_key,api_secret,api_passphrase
api_key         = os.environ.get("api_key")
api_secret      = os.environ.get("api_secret")
api_passphrase  = os.environ.get("api_passphrase")


def get_account(symbol):
  req_add = "/api/v1/account-overview?currency=" + symbol
  now = int(time.time() * 1000)
  str_to_sign = str(now) + "GET" + req_add
  signature = base64.b64encode(hmac.new(api_secret.encode("utf-8"), str_to_sign.encode("utf-8"), hashlib.sha256).digest())
  passphrase = base64.b64encode(hmac.new(api_secret.encode("utf-8"), api_passphrase.encode("utf-8"), hashlib.sha256).digest())
  Headers = {
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2",
    "status": "done"
    }
  R = requests.get("https://api-futures.kucoin.com" + req_add, headers = Headers).json()
  print(R)
  R = R["data"]["availableBalance"]
  # time.sleep(0.01)
  return({"balance":round(R,4)})
