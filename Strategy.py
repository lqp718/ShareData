# -*- coding: UTF-8 -*-
import datetime

import matplotlib.pyplot as plt
import tushare as ts
import pandas as pd
import numpy as np

from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY, date2num
from matplotlib.finance import candlestick_ohlc
# from pandas import DataFrame as DF

class StockStrategy():
    def __init__(self, code, start = None, end = None):
        tmStock  = ts.get_hist_data(code, start, end)
        idx = []
        for i in tmStock.index:
            idx.append(datetime.datetime.strptime(i, "%Y-%m-%d"))
        tmStock = tmStock.reindex(idx)
        tmStock.sort_index(ascending=True)

        self._stock = tmStock.sort_index(ascending=True)

    def stock_candlestick_ohlc(self, stick = "day", otherseries = None):
        '''
        这个函数用于绘制股票的k线图，默认绘制日k，也可通过改变stick绘制周k，月k及年k
        otherseries 参数可用于绘制均线，如：
        self.stock_candlestick_ohlc(otherseries = ["ma5", "ma10", "ma20"])
        其中"ma5", "ma10", "ma20" 是通过get_hist_data 函数获取股票数据时默认的参数，分别代表5日均值，10日均值，20日均值，
        如果想获得其他均值可通过stock_average 实现。
        '''
        mondays = WeekdayLocator(MONDAY)
        alldays = DayLocator()     
        #dayFormatter = DateFormatter('%d')

        transdat = self._stock.loc[:,["open", "high", "low", "close"]]
        if (type(stick) == str):
            if stick == "day":
                plotdat = transdat
                stick = 1 
            elif stick in ["week", "month", "year"]:
                if stick == "week":
                    transdat["week"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[1]) 
                elif stick == "month":
                    transdat["month"] = pd.to_datetime(transdat.index).map(lambda x: x.month) 
                transdat["year"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[0]) 
                grouped = transdat.groupby(list(set(["year",stick]))) 
                plotdat = pd.DataFrame({"open": [], "high": [], "low": [], "close": []})

                for name, group in grouped:
                    plotdat = plotdat.append(pd.DataFrame({"open": group.iloc[0,0],
                                                "high": max(group.high),
                                                "low": min(group.low),
                                                "close": group.iloc[-1,3]},
                                               index = [group.index[0]]))
                if stick == "week": stick = 5
                elif stick == "month": stick = 30
                elif stick == "year": stick = 365

        elif (type(stick) == int and stick >= 1):
            transdat["stick"] = [np.floor(i / stick) for i in range(len(transdat.index))]
            grouped = transdat.groupby("stick")
            plotdat = pd.DataFrame({"open": [], "high": [], "low": [], "close": []}) 
            for name, group in grouped:
                plotdat = plotdat.append(pd.DataFrame({"open": group.iloc[0,0],
                                            "high": max(group.high),
                                            "low": min(group.low),
                                            "close": group.iloc[-1,3]},
                                           index = [group.index[0]]))

        else:
            raise ValueError('Valid inputs to argument "stick" include the strings "day", "week", "month", "year", or a positive integer')

        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)
        if plotdat.index[-1] - plotdat.index[0] < pd.Timedelta('730 days'):
            weekFormatter = DateFormatter('%b %d')
            ax.xaxis.set_major_locator(mondays)
            ax.xaxis.set_minor_locator(alldays)
        else:
            weekFormatter = DateFormatter('%b %d, %Y')
        ax.xaxis.set_major_formatter(weekFormatter)

        ax.grid(True)

        candlestick_ohlc(ax, list(zip(list(date2num(plotdat.index.tolist())), plotdat["open"].tolist(), plotdat["high"].tolist(),
                          plotdat["low"].tolist(), plotdat["close"].tolist())),
                          colorup = "red", colordown = "green", width = stick * .4)

        if otherseries != None:
            if type(otherseries) != list:
                otherseries = [otherseries]
            self._stock.loc[:,otherseries].plot(ax = ax, lw = 1.3, grid = True)

        ax.xaxis_date()
        ax.autoscale_view()
        plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

        plt.show()

    def stock_return(self, draw = True):
        '''
        这个函数用于绘制当前股票的回报率, 并更新self._stock['return']
        return[t,0] = price[t] / price[0],
        可用于分析每只股票在周期开始以来的盈利状况。
        '''
        s_close = pd.DataFrame({"close": self._stock['close']})
        self._stock['return'] = s_close.apply(lambda x: x / x[0])
        if draw:
            self._stock['return'].plot(grid = True).axhline(y = 1, color = "black", lw = 2)
            plt.show()

    def stock_change(self, draw = True):
        '''
        这个函数用于绘制当前股票每个交易日的变化情况, 并更新self._stock['change']
        change[t] = log(price[t]) - log(price[t-1])
        使用对数差值的好处在于，这种差值可以理解为股价的百分比变化，且不依赖于计算过程中分数的分母。
        '''
        s_close = pd.DataFrame({"close": self._stock['close']})
        self._stock['change'] = s_close.apply(lambda x: np.log(x) - np.log(x.shift(1)))
        if draw:
            self._stock['change'].plot(grid = True).axhline(y = 0, color = "black", lw = 2)
            plt.show()

    def stock_average(self, average = [], draw = True):
        '''
        这个函数用于绘制相应股票的均值曲线，并更新self._stock中的均线值
        传入参数为list，如：
        ["5", "10", "20", "50", "100"]
        注：list 中的元素只能是字串，且不可包含字母及符号。
        '''
        if average:
            mals = [cls for cls in self._stock.columns if 'ma' in cls]

            for i, sa in enumerate(average):
                ma_sa = "ma%s" % sa
                average[i] = ma_sa
                if ma_sa in mals:
                    continue
                self._stock[ma_sa] = np.round(self._stock["close"].rolling(window = int(sa), center = False).mean(), 2)

            if draw:
                self.stock_candlestick_ohlc(otherseries = average)

    def stock_regime(self, a1 = "5", a2 = "20", draw = True):
        '''
        利用移动均线法判断当前股市状态并绘制股市状态图，同时更新self._stock
        其中a1及a2 只能是字串，并且只能包含数字，且a1 < a2
        '''
        self.stock_average(average = [a1, a2], draw = False)
        self._stock["ma%s - ma%s" % (a1,a2)] = self._stock["ma%s" % a1] - self._stock["ma%s" % a2]
        self._stock["Regime"] = np.where(self._stock["ma%s - ma%s" % (a1,a2)] > 0, 1, 0)
        self._stock["Regime"] = np.where(self._stock["ma%s - ma%s" % (a1,a2)] < 0, -1, self._stock["Regime"])

        if draw:
            self._stock["Regime"].plot(grid = True).axhline(y = 0, color = "black", lw = 2)
            plt.show()

    def stock_singal(self, a1 = "5", a2 = "20", draw = True):
        '''
        根据股市状态绘制买卖信号图，1 代表买入，-1 代表卖出，0代表无操作
        '''
        self.stock_regime(a1, a2, draw = False)
        regime_orig = self._stock.ix[-1, "Regime"]
        self._stock.ix[-1, "Regime"] = 0
        #
        # 用当前日期的Regime 减去前一天的Regime，结果大于零则代表当前是a1均线上穿a2均线，为牛市行情，反之为熊市行情
        #
        self._stock["Signal"] = np.sign(self._stock["Regime"] - self._stock["Regime"].shift(1))
        self._stock.ix[-1, "Regime"] = regime_orig
        if draw:
            self._stock["Signal"].plot(grid = True)
            plt.show()

    def stock_backtest(self):
        self.stock_singal(draw = False)
        stock_signals_tmp = pd.concat([
                pd.DataFrame({"Price": self._stock.loc[self._stock["Signal"] == 1, "close"],
                             "Regime": self._stock.loc[self._stock["Signal"] == 1, "Regime"],
                             "Signal": "Buy"}),
                pd.DataFrame({"Price": self._stock.loc[self._stock["Signal"] == -1, "close"],
                             "Regime": self._stock.loc[self._stock["Signal"] == -1, "Regime"],
                             "Signal": "Sell"}),
            ])
        stock_signals_tmp.sort_index(inplace = True)

        #
        # 为了完成一个完整周期的数据回测，最后一笔交易一定是卖出交易，所以当判断出最后一行是买入交易时，应将最后一行数据移除
        #
        if stock_signals_tmp.ix[-1,"Signal"] == "Buy":
            stock_signals = stock_signals_tmp.ix[:-1]
        else:
            stock_signals = stock_signals_tmp

        stock_long_profits = pd.DataFrame({
                # Price 代表每次交易的买入价格
                "Price": stock_signals.loc[(stock_signals["Signal"] == "Buy") &
                                          stock_signals["Regime"] == 1, "Price"],
                # Profit 代表卖出股票时每股股票的盈利值（即卖出价格-买入价格）
                "Profit": pd.Series(stock_signals["Price"] - stock_signals["Price"].shift(1)).loc[
                    stock_signals.loc[(stock_signals["Signal"].shift(1) == "Buy") & (stock_signals["Regime"].shift(1) == 1)].index
                ].tolist(),
                # End Date 代表卖出股票的日期
                "End Date": stock_signals["Price"].loc[
                    stock_signals.loc[(stock_signals["Signal"].shift(1) == "Buy") & (stock_signals["Regime"].shift(1) == 1)].index
                ].index
            })
        tradeperiods = pd.DataFrame({"Start": stock_long_profits.index,
                            "End": stock_long_profits["End Date"]})
        stock_long_profits["Low"] = tradeperiods.apply(lambda x: min(self._stock.loc[x["Start"]:x["End"], "low"]), axis = 1)

        cash = 100000
        stock_backtest = pd.DataFrame({"Start Port. Value": [],
                                 "End Port. Value": [],
                                 "End Date": [],
                                 "Shares": [],
                                 "Share Price": [],
                                 "Trade Value": [],
                                 "Profit per Share": [],
                                 "Total Profit": [],
                                 "Stop-Loss Triggered": []})
        port_value = .5 # 每次交易控制在总成本的50%
        batch = 100     # 一手股票为100股
        stoploss = .1   # 止损系数当当前交易最低价格低于买入价格的90% 的时候终止交易
        for index, row in stock_long_profits.iterrows():
            batches = np.floor(cash * port_value) // np.ceil(batch * row["Price"]) # batches 代表当次交易所能购买的最多手数
            trade_val = batches * batch * row["Price"] #当前交易的总金额
            if row["Low"] < (1 - stoploss) * row["Price"]:   # 如果当前的最低价格已经低于买入价格的80%则终止当前交易
                # share_profit 代表每股收益, 当达到止损条件时(即当前交易时段股票最低价格已经低于买入价格的90%) 卖出股票，所以此时每股收益为负值
                share_profit = np.round((1 - stoploss) * row["Price"], 2) - row["Price"]
                stop_trig = True
            else:
                share_profit = row["Profit"]
                stop_trig = False
            print share_profit
            profit = share_profit * batches * batch

            stock_backtest = stock_backtest.append(pd.DataFrame({
                        "Start Port. Value": cash,
                        "End Port. Value": cash + profit,
                        "End Date": row["End Date"],
                        "Shares": batch * batches,
                        "Share Price": row["Price"],
                        "Trade Value": trade_val,
                        "Profit per Share": share_profit,
                        "Total Profit": profit,
                        "Stop-Loss Triggered": stop_trig
                    }, index = [index]))
            cash = max(0, cash + profit)
        stock_backtest["End Port. Value"].plot()
        plt.show()

# test code>>>
if __name__ == '__main__':
    sStrategy = StockStrategy("600050", "2015-01-05")
    # # sStrategy.stock_candlestick_ohlc()
    # # sStrategy.stock_return()
    # # sStrategy.stock_change()
    sStrategy.stock_singal(draw = False)
    # print sStrategy._stock.loc[:, ["close", "low", "ma5", "ma20", "Regime", "Signal"]].to_json(orient = "index")
    sStrategy.stock_candlestick_ohlc(otherseries = ["ma5", "ma20", "Regime", "Signal"])
    sStrategy.stock_backtest()
# test code<<<