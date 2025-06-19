import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time

# === CONFIGURATION ===
login = 210123439    # replace with your MT5 account ID
password = "Zfw!&aNC&cSNu3u"
server = "Exness-MT5Trial9"  # adjust as needed

# USD currency pairs to trade
usd_pairs = ["EURUSDm", "GBPUSDm", "USDJPYm", "USDCHFm", "USDCADm", "AUDUSDm",
             "NZDUSDm", "XAUUSDm"]

lot = 0.1
distance = 50  # points
slippage = 5
news_time = datetime(2025, 6, 19, 14, 31) # set your actual news time

# === INITIALIZE MT5 ===
if not mt5.initialize(login=login, password=password, server=server):
    print("Initialization failed:", mt5.last_error())
    quit()

# === WAIT FOR NEWS TIME ===
print("Waiting for scheduled news release at", news_time)
while datetime.now() < news_time - timedelta(seconds=5):
    time.sleep(1)

# === TRADE EACH USD PAIR ===
for symbol in usd_pairs:
    # Ensure symbol is available in Market Watch
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}")
        continue

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"Failed to get tick for {symbol}")
        continue

    ask = tick.ask
    bid = tick.bid

    # Calculate entry prices
    buy_price = ask + distance * mt5.symbol_info(symbol).point
    sell_price = bid - distance * mt5.symbol_info(symbol).point

    # Buy Stop
    buy_result = mt5.order_send({
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY_STOP,
        "price": round(buy_price, 5),
        "sl": round(buy_price - 30 * mt5.symbol_info(symbol).point, 5),
        "tp": round(buy_price + 60 * mt5.symbol_info(symbol).point, 5),
        "deviation": slippage,
        "magic": 1000,
        "comment": f"News Buy Stop {symbol}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    })

    # Sell Stop
    sell_result = mt5.order_send({
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL_STOP,
        "price": round(sell_price, 5),
        "sl": round(sell_price + 30 * mt5.symbol_info(symbol).point, 5),
        "tp": round(sell_price - 60 * mt5.symbol_info(symbol).point, 5),
        "deviation": slippage,
        "magic": 1001,
        "comment": f"News Sell Stop {symbol}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    })

    print(f"{symbol}: Buy result:", buy_result)
    print(f"{symbol}: Sell result:", sell_result)

# === SHUTDOWN ===
mt5.shutdown()
