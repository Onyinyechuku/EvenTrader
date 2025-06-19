import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import csv
import os

# === CONFIGURATION ===
login = 210123439
password = "Zfw!&aNC&cSNu3u"
server = "Exness-MT5Trial9"

currency_pairs = {
    "usd_pairs": ["EURUSDm", "GBPUSDm", "USDJPYm", "USDCHFm", "USDCADm", "AUDUSDm", "NZDUSDm", "XAUUSDm"],
    "gbp_pairs": ["EURGBPm", "GBPJPYm", "GBPCHFm", "GBPCADm", "GBPAUDm", "GBPNZDm"]
}

lot = 0.1
distance = 50  # in points
slippage = 5
cancel_after_minutes = 15  # Cancel pending orders after this time
risk_margin_threshold = 50.0  # Minimum free margin to allow trading
log_file = "trade_log.csv"
news_time = datetime(2025, 6, 19, 17, 23)

# === INITIALIZE MT5 ===
if not mt5.initialize(login=login, password=password, server=server):
    print("Initialization failed:", mt5.last_error())
    quit()

# === CHECK MARGIN BEFORE TRADING ===
account_info = mt5.account_info()
if account_info is None:
    print("Failed to retrieve account info")
    mt5.shutdown()
    quit()

if account_info.margin_free < risk_margin_threshold:
    print("Not enough free margin to trade.")
    mt5.shutdown()
    quit()

# === LOGGING SETUP ===
if not os.path.exists(log_file):
    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Symbol", "OrderType", "Price", "SL", "TP", "Result", "Comment"])

def log_trade(symbol, order_type, price, sl, tp, result, comment):
    with open(log_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), symbol, order_type, price, sl, tp, result, comment])

# === WAIT FOR NEWS TIME ===
print("Waiting for news release at", news_time)
while datetime.now() < news_time - timedelta(seconds=5):
    time.sleep(1)

# === FUNCTION TO TRADE SYMBOL ===
def trade_symbol(symbol, magic_base):
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}")
        return

    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if not info or not tick:
        print(f"Missing data for {symbol}")
        return

    digits = info.digits
    point = info.point
    ask = tick.ask
    bid = tick.bid

    buy_price = round(ask + distance * point, digits)
    sell_price = round(bid - distance * point, digits)

    # Buy Stop Order
    buy_result = mt5.order_send({
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY_STOP,
        "price": buy_price,
        "sl": round(buy_price - 30 * point, digits),
        "tp": round(buy_price + 60 * point, digits),
        "deviation": slippage,
        "magic": magic_base,
        "comment": f"News Buy Stop {symbol}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    })
    log_trade(symbol, "BUY_STOP", buy_price, buy_price - 30 * point, buy_price + 60 * point,
              buy_result.retcode, buy_result.comment)

    # Sell Stop Order
    sell_result = mt5.order_send({
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL_STOP,
        "price": sell_price,
        "sl": round(sell_price + 30 * point, digits),
        "tp": round(sell_price - 60 * point, digits),
        "deviation": slippage,
        "magic": magic_base + 1,
        "comment": f"News Sell Stop {symbol}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    })
    log_trade(symbol, "SELL_STOP", sell_price, sell_price + 30 * point, sell_price - 60 * point,
              sell_result.retcode, sell_result.comment)

# === TRADE ALL CURRENCY PAIRS ===
pair_traded = False

# Try USD pairs first
for symbol in currency_pairs["gbp_pairs"]:
    if not pair_traded:
        print(f"Trying to trade: {symbol}")
        trade_symbol(symbol, magic_base=1000)
        pair_traded = True
        break  # Stop after trading the first one

# If you prefer GBP over USD, reverse the order
# or you can prioritize based on spread, volatility, etc.


# === WAIT, THEN CANCEL PENDING ORDERS ===
cancel_time = news_time + timedelta(minutes=cancel_after_minutes)
print(f"Waiting {cancel_after_minutes} minutes before cancelling untriggered pending orders...")
while datetime.now() < cancel_time:
    time.sleep(10)

# Cancel all pending orders placed by this script (with specific magic numbers)
def cancel_pending_orders():
    orders = mt5.orders_get()
    if orders is None:
        print("Failed to get pending orders.")
        return
    for order in orders:
        if order.magic in range(1000, 3000):  # covers both USD and GBP pair magic numbers
            cancel = mt5.order_send({
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
            })
            status = "Success" if cancel.retcode == mt5.TRADE_RETCODE_DONE else f"Failed: {cancel.retcode}"
            print(f"Cancelled Order {order.ticket} ({order.symbol}): {status}")
            log_trade(order.symbol, "CANCEL", order.price_open, "", "", cancel.retcode, status)

cancel_pending_orders()

# === SHUTDOWN ===
mt5.shutdown()
