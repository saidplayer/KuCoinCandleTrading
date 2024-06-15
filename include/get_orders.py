import requests, json, time, datetime
import base64, hashlib, hmac, os
from dotenv import load_dotenv


load_dotenv()
global api_key,api_secret,api_passphrase
api_key         = os.environ.get("api_key")
api_secret      = os.environ.get("api_secret")
api_passphrase  = os.environ.get("api_passphrase")


def get_all_orders(pair, lot_size):
  orders = []
  try:
    R = get_pending_orders(pair)
    for order in R:
      orders.append([order["clientOid"], order["status"], order["filledSize"], order["endAt"], order["id"], float(order["price"]), float(order["createdAt"])])
  except Exception as err:
    print("A: " + str(err))
  try:
    R = get_triggered_orders(pair)
    for order in R:
      if order["type"] == "market" or True:
        if order["filledSize"] != 0: 
          order["price"] = float(order["dealValue"])/float(order["dealSize"]) / lot_size
      orders.append([order["clientOid"], order["status"], order["filledSize"], order["endAt"], order["id"], float(order["price"]), float(order["createdAt"])])

  except Exception as err:
    print("B: " + str(err))
  try:
    R = get_open_orders(pair)
    for order in R:
      orders.append([order["clientOid"], order["status"], order["filledSize"], order["endAt"], order["id"], float(order["price"]), float(order["createdAt"])])
  except Exception as err:
    print("C: " + str(err))
  return(orders)


def get_pending_orders(pair):
  req_add = "/api/v1/stopOrders?symbol=" + pair + "&status=active"
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
    "status": "active"
    }
  R = requests.get("https://api-futures.kucoin.com" + req_add, headers = Headers).json()["data"]["items"]
  # time.sleep(0.01)
  return(R[:20])


def get_triggered_orders(pair):
  req_add = "/api/v1/orders?symbol=" + pair + "&status=done"
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
  R = requests.get("https://api-futures.kucoin.com" + req_add, headers = Headers).json()["data"]["items"]
  # time.sleep(0.01)
  return(R[:20])


def get_open_orders(pair):
  req_add = "/api/v1/orders?symbol=" + pair + "&status=active"
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
  R = requests.get("https://api-futures.kucoin.com" + req_add, headers = Headers).json()["data"]["items"]
  # time.sleep(0.01)
  return(R[:20])


def get_positions(pair):
  req_add = "/api/v1/positions?symbol=" + pair
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
  R = requests.get("https://api-futures.kucoin.com" + req_add, headers = Headers).json()["data"]
  # time.sleep(0.01)
  return(R)
