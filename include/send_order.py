import requests, json, time, datetime
import base64, hashlib, hmac, os
from dotenv import load_dotenv

load_dotenv()
global api_key,api_secret,api_passphrase
api_key = os.environ.get("api_key")
api_secret = os.environ.get("api_secret")
api_passphrase = os.environ.get("api_passphrase")


def send_stoplimit_order(symbol,side,price,size_base,CID):
  price = round(price,5)

  req_add = '/api/v1/orders'
  Body={"clientOid":CID,"side":side,"symbol":symbol,"type":"limit","price":str(price),"size":str(size_base),"stop":"entry","stopPrice":str(price*0.98)}

  now = int(time.time() * 1000)
  str_to_sign = str(now) + 'POST' + req_add + json.dumps(Body)
  signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
  passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
  Headers = {
    "Content-type": "application/json",
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2",
    }
  R = requests.post('https://api.kucoin.com' + req_add, headers = Headers, data=json.dumps(Body)).json()
  # time.sleep(0.01)
  return R


def send_limit_order(symbol,side,price,size_base,CID):
  price = round(price,5)
  req_add = '/api/v1/orders'
  Body={"clientOid":CID,"side":side,"symbol":symbol,"type":"limit","price":str(price),"size":str(size_base)}
  now = int(time.time() * 1000)
  str_to_sign = str(now) + 'POST' + req_add + json.dumps(Body)
  signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
  passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
  Headers = {
    "Content-type": "application/json",
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2",
    }
  R = requests.post('https://api.kucoin.com' + req_add, headers = Headers, data=json.dumps(Body)).json()
  # time.sleep(0.01)
  return R


def send_market_order(symbol,side,size_base,CID):
  req_add = '/api/v1/orders'
  Body={"clientOid":CID,"side":side,"symbol":symbol,"type":"market","size":str(size_base)}
  now = int(time.time() * 1000)
  str_to_sign = str(now) + 'POST' + req_add + json.dumps(Body)
  signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
  passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
  Headers = {
    "Content-type": "application/json",
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2",
    }
  R = requests.post('https://api.kucoin.com' + req_add, headers = Headers, data=json.dumps(Body)).json()
  # time.sleep(0.01)
  return R
