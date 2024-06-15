import requests, json, time, datetime
import base64, hashlib, hmac, os
from dotenv import load_dotenv

load_dotenv()
global api_key,api_secret,api_passphrase
api_key         = os.environ.get("api_key")
api_secret      = os.environ.get("api_secret")
api_passphrase  = os.environ.get("api_passphrase")

def get_fills(pair,page,start,end):
  req_add = "/api/v1/fills?currentPage=" + page + "&startAt=" + start + "&endAt=" + end
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
  return(R)


def get_report(pair,start_time,end_time,details=False):
  pages = []
  for i in range(round((end_time-start_time)/24/3600)+1):
    start = (start_time + i*24*3600) * 1000
    end   = min([start_time + (i+1)*24*3600, end_time]) * 1000
    pageNum = 1
    while True:
      time.sleep(1)
      resp = get_fills(pair, str(pageNum), str(round(start)), str(round(end)))
      pages.append(resp["items"])
      if resp["totalPage"] > pageNum:
        pageNum = pageNum + 1
      else:
        break
  fills = []
  for page in pages:
    for row in page:
      fills.append(row)

  if details: return(fills)

  fees = 0
  bought = []
  sold = []
  for fill in fills:
    fees = fees + float(fill["fee"])
    if fill["side"] == "buy":
      [bought.append(float(fill["value"])/int(fill["size"])) for x in range(int(fill["size"]))]
    else:
      [sold.append(float(fill["value"])/int(fill["size"])) for x in range(int(fill["size"]))]
  n = min(len(bought),len(sold))
  bought = bought[:n]
  sold   = sold[:n]
  bought = sum(bought)
  sold   = sum(sold)

  return([len(fills)/2, sold - bought, fees, sold-bought-fees])
