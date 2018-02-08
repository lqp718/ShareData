# -*- coding: UTF-8 -*-
import datetime

import matplotlib.pyplot as plt
import tushare as ts
import pandas as pd
import numpy as np

from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY, date2num
from matplotlib.finance import candlestick_ohlc

def ma_crossover_orders(stocks, fast, slow):
    fast_str = str(fast) + 'd'
    slow_str = str(slow) + 'd'
    ma_diff_str = fast_str + '-' + slow_str
 
    trades = pd.DataFrame({"Price": [], "Regime": [], "Signal": []})
    for s in stocks:
        s[1][fast_str] = np.round(s[1]["close"].rolling(window = fast, center = False).mean(), 2)
        s[1][slow_str] = np.round(s[1]["close"].rolling(window = slow, center = False).mean(), 2)
        s[1][ma_diff_str] = s[1][fast_str] - s[1][slow_str]
 
        s[1]["Regime"] = np.where(s[1][ma_diff_str] > 0, 1, 0)
      
        s[1]["Regime"] = np.where(s[1][ma_diff_str] < 0, -1, s[1]["Regime"])
        
        regime_orig = s[1].ix[-1, "Regime"]
        s[1].ix[-1, "Regime"] = 0
        s[1]["Signal"] = np.sign(s[1]["Regime"] - s[1]["Regime"].shift(1))
        
        s[1].ix[-1, "Regime"] = regime_orig
 
        signals = pd.concat([
            pd.DataFrame({"Price": s[1].loc[s[1]["Signal"] == 1, "close"],
                         "Regime": s[1].loc[s[1]["Signal"] == 1, "Regime"],
                         "Signal": "Buy"}),
            pd.DataFrame({"Price": s[1].loc[s[1]["Signal"] == -1, "close"],
                         "Regime": s[1].loc[s[1]["Signal"] == -1, "Regime"],
                         "Signal": "Sell"}),
        ])
        signals.index = pd.MultiIndex.from_product([signals.index, [s[0]]], names = ["Date", "Symbol"])
        trades = trades.append(signals)
 
    trades.sort_index(inplace = True)
    trades.index = pd.MultiIndex.from_tuples(trades.index, names = ["Date", "Symbol"])
 
    return trades

def get_stock(code, start, end = None):
    tmStock  = ts.get_hist_data(code, start, end)
    idx = []
    for i in tmStock.index:
        idx.append(datetime.datetime.strptime(i, "%Y-%m-%d"))
    tmStock = tmStock.reindex(idx)
    tmStock.sort_index(ascending=True)

    _stock = tmStock.sort_index(ascending=True)
    return _stock

def backtest(signals, cash, port_value = .5, batch = 100):
    SYMBOL = 1 
    portfolio = dict()   
    port_prices = dict()  
    print signals
    results = pd.DataFrame({"Start Cash": [],
                            "End Cash": [],
                            "Portfolio Value": [],
                            "Type": [],
                            "Shares": [],
                            "Share Price": [],
                            "Trade Value": [],
                            "Profit per Share": [],
                            "Total Profit": []})
 
    for index, row in signals.iterrows():
        print index
        shares = portfolio.setdefault(index[SYMBOL], 0)
        print shares
        trade_val = 0
        batches = 0
        cash_change = row["Price"] * shares   
        portfolio[index[SYMBOL]] = 0  
 
        old_price = port_prices.setdefault(index[SYMBOL], row["Price"])
        portfolio_val = 0
        for key, val in portfolio.items():
            portfolio_val += val * port_prices[key]
 
        if row["Signal"] == "Buy" and row["Regime"] == 1: 
            batches = np.floor((portfolio_val + cash) * port_value) // np.ceil(batch * row["Price"]) 
            trade_val = batches * batch * row["Price"] 
            cash_change -= trade_val 
            portfolio[index[SYMBOL]] = batches * batch  
            port_prices[index[SYMBOL]] = row["Price"]   
            old_price = row["Price"]
        elif row["Signal"] == "Sell" and row["Regime"] == -1: 
            pass
 
        pprofit = row["Price"] - old_price  
        
        results = results.append(pd.DataFrame({
                "Start Cash": cash,
                "End Cash": cash + cash_change,
                "Portfolio Value": cash + cash_change + portfolio_val + trade_val,
                "Type": row["Signal"],
                "Shares": batch * batches,
                "Share Price": row["Price"],
                "Trade Value": abs(cash_change),
                "Profit per Share": pprofit,
                "Total Profit": batches * batch * pprofit
            }, index = [index]))
        cash += cash_change 
 
    results.sort_index(inplace = True)
    results.index = pd.MultiIndex.from_tuples(results.index, names = ["Date", "Symbol"])
 
    return results

Signal = ma_crossover_orders([("Liantong", get_stock("600050", start = "2015-01-05"))],
                    # ("Fangzheng", get_stock("601901", start = "2015-01-05")),
                    # ("Pingan", get_stock("000001", start = "2015-01-05")),
                    # ("Sanwei", get_stock("002115", start = "2015-01-05"))],
                    fast = 5,
                    slow = 20)

print Signal

# bk = backtest(Signal, 20000)


# bk["Portfolio Value"].groupby(level = 0).apply(lambda x: x[-1]).plot()
# plt.show()