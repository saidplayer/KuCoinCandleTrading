import requests, json

def get_tick(pair):
  try:
    R = requests.get("https://api-futures.kucoin.com/api/v1/contracts/" + pair).json()["data"]
    # print(R)
    max_leverage = R["maxLeverage"]
    fee_rate = R["makerFeeRate"]
    tick_size = R["tickSize"]
    price = R["lastTradePrice"]
    return({"max_leverage":max_leverage, "lot_size":0.01, "fee_rate": fee_rate, "tick_size": tick_size, "price": price})
  except Exception as err:
    print(str(error))