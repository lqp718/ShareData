# -*- coding: utf-8 -*-
import config as cfg
import tushare as ts
import datetime
import time
import random

date = datetime.datetime.strptime(cfg.StartDate, "%Y-%m-%d")
delta = datetime.timedelta(days=1)
i = 0

while True:
	t = random.uniform(1, 5)
	try:
		print date.strftime("%Y-%m-%d")
		print ts.get_k_data(cfg.ShareCode, start=date.strftime("%Y-%m-%d"), end=date.strftime("%Y-%m-%d"), autype = None)
		df = ts.get_tick_data(cfg.ShareCode, date=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
		if len(df) > 3: # src = "sn"
			SortDf = df.sort_index(ascending=False,inplace=False)#.sort_values(by = 'time', axis = 0,ascending = True)
			SortDf['type'] = SortDf['type'].replace("买盘", "buy").replace("卖盘", "sel").replace("中性盘", "neu")
			print SortDf

		if date.strftime("%Y-%m-%d") == datetime.datetime.now().strftime('%Y-%m-%d'):
			break
		time.sleep(t)
		date = date + delta
		i = i + 1
		if i == 10:
			i = 0
			time.sleep(10)
	except:
		with open("fail.txt", "w") as f:
			f.write(date.strftime("%Y-%m-%d"))
		time.sleep(t)
		date = date + delta
		pass