import requests, json, time
def get_candle(pair,time_frame):
  start_time = round(time.time() * 1000 - ((time_frame + 2) * 60000))
  price = requests.get("https://api-futures.kucoin.com/api/v1/kline/query?symbol=" + pair + "&granularity=" + str(time_frame) + "&from=" + str(start_time)).json()
  price = price['data']
  price = price[len(price)-1]
  epoch = float(price[0])
  high  = float(price[2])
  low   = float(price[3])
  price = float(price[4])
  return({"time": epoch, "price": price, "high": high, "low": low})
