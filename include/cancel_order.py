import requests, json, time, datetime
import base64, hashlib, hmac, os
from dotenv import load_dotenv

load_dotenv()
global api_key,api_secret,api_passphrase
api_key = os.environ.get("api_key")
api_secret = os.environ.get("api_secret")
api_passphrase = os.environ.get("api_passphrase")


def cancel_all_orders(pair):
  req_addr = '/api/v1/stopOrders?symbol=' + pair
  now = int(time.time() * 1000)
  str_to_sign = str(now) + 'DELETE' + req_addr
  signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
  passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
  Headers = {
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2"
    }
  R = requests.delete("https://api-futures.kucoin.com" + req_addr, headers = Headers).json()
  time.sleep(0.01)

  req_addr = '/api/v1/orders?symbol=' + pair
  now = int(time.time() * 1000)
  str_to_sign = str(now) + 'DELETE' + req_addr
  signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
  passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
  Headers = {
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2"
    }
  R = requests.delete("https://api-futures.kucoin.com" + req_addr, headers = Headers).json()

  # time.sleep(0.01)



def cancel_order(oid):
  req_addr = '/api/v1/orders/' + oid
  now = int(time.time() * 1000)
  str_to_sign = str(now) + 'DELETE' + req_addr
  signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
  passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
  Headers = {
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2"
    }
  R = requests.delete("https://api-futures.kucoin.com" + req_addr, headers = Headers).json()
  # time.sleep(0.01)
  return R
