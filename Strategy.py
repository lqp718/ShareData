# -*- coding: UTF-8 -*-
import datetime

import matplotlib.pyplot as plt
import tushare as ts
import pandas as pd
import numpy as np
import logging

from Database import DB
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY, date2num
from matplotlib.finance import candlestick_ohlc
# from pandas import DataFrame as DF

class StockStrategy():
    def __init__(self, code, start = None, end = None):
        self._code = code
        self._start_date = start
        self._end_date = end
        self._stock = None
        self._cash = 0
        self._property = self._cash
        self._holding_stock = 0
        self.GetShareData()

    def __del__(self):
        pass

    def GetShareData(self):
        database = DB("MyShare", self._code)
        d_start = datetime.datetime.strptime(self._start_date, "%Y-%m-%d")
        i, result = database.find(_filter = {'date' : {"$gte": d_start}}, _projection = {'_id': False, 'tick': False})
        #i = 0
        if i != 0:
            self._stock = database.ConstructionDf(result).sort_index(ascending=True)
        else:
            logging.debug("Can't get the share data from database, try to get through ts")
            tmStock  = ts.get_hist_data(self._code, self._start_date, self._end_date)
            idx = []
            for i in tmStock.index:
                idx.append(datetime.datetime.strptime(i, "%Y-%m-%d"))
            tmStock = tmStock.reindex(idx)
            self._stock = tmStock.sort_index(ascending=True)

    def stock_candlestick_ohlc(self, event = None, stick = "day", otherseries = None):
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
            weekFormatter = DateFormatter('%b %d, %Y')
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
        # if event is None:
        #     plt.show()
        # else:
        #     plt.show(block = False)
        #     while event.isSet():
        #         time.sleep(1)

    def stock_return(self, event = None, draw = True):
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

    def stock_change(self, event = None, draw = True):
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

    def stock_average(self, event = None, average = [], draw = True):
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

    def stock_regime(self, event = None, a1 = "5", a2 = "20", draw = True):
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

    def stock_singal(self, event = None, a1 = "5", a2 = "20", draw = True):
        '''
        根据股市状态绘制买卖信号图，1 代表买入，-1 代表卖出，0代表无操作
        '''
        self.stock_regime(event = None, a1 = a1, a2 = a2, draw = False)
        regime_orig = self._stock.ix[-1, "Regime"]
        self._stock.ix[-1, "Regime"] = 0
        #
        # 用当前日期的Regime 减去前一天的Regime，结果大于零则代表当前是a1均线上穿a2均线，为牛市行情，反之为熊市行情
        #
        self._stock["Signal"] = np.sign(self._stock["Regime"] - self._stock["Regime"].shift(1))
        self._stock.ix[-1, "Regime"] = regime_orig
        if draw:
            self.stock_candlestick_ohlc(otherseries = ["ma" + a1, "ma" + a2, "Signal"])

    def stock_buy(self, batches, price):
        trade_val = batches * 100 * price
        if trade_val <= self._cash:
            fees = np.floor(trade_val * 1.8 / 10000)
            if fees < 5:
                fees = 5
            self._cash = self._cash - trade_val - fees
            self._holding_stock = batches
            self._property = self._cash + self._holding_stock * price * 100
            print self._property
        else:
            logging.error("Don't have enough cash!!!")


    def stock_sell(self, batches, price):
        if batches <= self._holding_stock:
            trade_val = batches * 100 * price
            fees = np.floor(trade_val * 1.8 / 10000)
            if fees < 5:
                fees = 5
            fees = fees + np.floor(trade_val * 1 / 1000)

            self._cash = self._cash + trade_val - fees
            self._holding_stock = self._holding_stock - batches
            self._property = self._cash + self._holding_stock * price * 100
            print self._property
        else:
            logging.error("Don't have enough stock!!!")

    def stock_backtest(self, event = None, cash_start = 200000, a1 = "10", a2 = "30"):
        self.stock_singal(a1 = a1, a2 = a2, draw = False)
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
        self._cash = cash_start
        self._property = cash_start
        stock_backtest = pd.DataFrame({"Start Port. Value": [],
                                        "End Port. Value": [],
                                        "Shares": [],
                                        "Share Price": [],
                                        "Total Profit": []})
        port_value = .5 # 每次交易控制在总成本的50%
        batch = 100     # 一手股票为100股
        for index, row in stock_signals.iterrows():
            print row
            if row["Signal"] == "Buy":
                batches = np.floor(self._cash * port_value) // np.ceil(batch * row["Price"]) # batches 代表当次交易所能购买的最多手数
                self.stock_buy(batches, row['Price'])
            elif row["Signal"] == "Sell":
                batches = self._holding_stock 
                if batches != 0:
                    self.stock_sell(batches, row['Price'])

            stock_backtest = stock_backtest.append(pd.DataFrame({
                        "Start Port. Value": self._cash,
                        "End Port. Value": self._property,
                        "Shares": self._holding_stock,
                        "Share Price": row["Price"],
                        "Total Profit": self._property - cash_start,
                    }, index = [index]))
        stock_backtest["End Port. Value"].plot()
        plt.show()

# test code>>>
if __name__ == '__main__':
    sStrategy = StockStrategy("600050", "2015-01-05")
    # sStrategy.GetShareData()
    # sStrategy.stock_candlestick_ohlc(event = None)
    # sStrategy.stock_return()
    # sStrategy.stock_change()
    # sStrategy.stock_singal()
    # print sStrategy._stock.loc[:, ["close", "low", "ma5", "ma20", "Regime", "Signal"]].to_json(orient = "index")
    # sStrategy.stock_candlestick_ohlc(otherseries = ["ma5", "ma20", "Regime", "Signal"])
    sStrategy.stock_backtest()
# test code<<<