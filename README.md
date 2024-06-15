# KuCoin Candle Trading
KuCoin is a well known crypto trading platform. KuCoin provides an API with lots of possibilities for communicating data and orders. This is a crypto trading bot that I programmed some time ago.

### The story
I programmed this bot based on a very simple idea that someone had and wanted to test. My goal was to work with the KuCoin API and have some experience with opening, closing and trailing trades within time steps as low as minutes and seconds.

### Candle trading
The bot works like this: if trading conditions are true, it sets two limit orders: one buy order slightly above HIGH of the last 1-minute candle, and another  slightly below the LOW of the last 1-minute candle. Conditions include: beign at a specific period of the day, last 1-minute candle being larger than a threshold.

### Handling data
This was an experience where handling data and database was important. The API was not always responding in a timely manner. Therefore I decided to work with trade data stored in two places: 1) on the KuCoin platform, accessed through the API; and 2) locally. The data that I needed to use quickly were stored locally. I chose certain events, frequent enoughbut not delay-critical, to trigger syncronization of the local database with the one existing on the remote KuCoin database.

### GUI
I used Tkinter for designing GUI in Python. Tkinter is one of the most widely used libraries for creating Desktop Applications in Python, many developers find it easy to use, but the main problem is it requires a lot of time to create a beautiful GUI. That why I did not take the time to make it a beautiful, modern GUI. On the functionality level, however, the GUI that I designed turned out to be pretty clear and handy.

