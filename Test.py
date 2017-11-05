# from pymongo import MongoClient
# import config as cfg
# from pandas import DataFrame

# import datetime

# import tushare as ts


# conn = MongoClient()
# db = conn.MyShare
# Collection = db.get_collection(name = cfg.ShareCode)

# DataFrame.from_dict(Collection.find_one({"date":"2017-10-23"})['tick'], orient = 'index').sort_values(by = 'time', axis = 0, ascending = True)['price'].plot(grid=True)
# plt.show()

# for col in Collection.find():
#     print col["date"]
#     Collection.update_one({"date": col["date"]},{"$set": {"date": datetime.datetime.strptime(col["date"], "%Y-%m-%d")}})

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY, date2num
from matplotlib.finance import candlestick_ohlc
import tushare as ts
import pandas as pd
import numpy as np
import datetime

def pandas_candlestick_ohlc(dat, stick = "day", otherseries = None):
    mondays = WeekdayLocator(MONDAY)        
    alldays = DayLocator()     
    dayFormatter = DateFormatter('%d')

    transdat = dat.loc[:,["open", "high", "low", "close"]]
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
                      colorup = "black", colordown = "red", width = stick * .4)

    if otherseries != None:
        if type(otherseries) != list:
            otherseries = [otherseries]
        dat.loc[:,otherseries].plot(ax = ax, lw = 1.3, grid = True)

    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

    plt.show()

if __name__ == '__main__':
	Share  = ts.get_hist_data("600050", "2016-01-05", "2017-02-05")
	idx = []

	for i in Share.index:
		idx.append(datetime.datetime.strptime(i, "%Y-%m-%d"))
	Share = Share.reindex(idx)
	Share.sort_index(ascending=True,inplace=True)

	# Share_close = pd.DataFrame({"close": Share['close']})
	# print Share_close
	# Share_return = Share_close.apply(lambda x: x / x[0])
	# Share_change = Share_close.apply(lambda x: np.log(x) - np.log(x.shift(1)))
	# Share_return.plot(grid = True).axhline(y = 1, color = "black", lw = 2)
	# Share_change.plot(grid = True).axhline(y = 0, color = "black", lw = 2)

	Share["20d"] = np.round(Share["close"].rolling(window = 20, center = False).mean(), 2)
	Share["50d"] = np.round(Share["close"].rolling(window = 50, center = False).mean(), 2)
	Share["100d"] = np.round(Share["close"].rolling(window = 100, center = False).mean(), 2)
	pandas_candlestick_ohlc(Share, otherseries = ["ma5", "ma10", "ma20", "50d", "100d"])
#	plt.show()
#	pandas_candlestick_ohlc(Share)