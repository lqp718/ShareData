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
#	try:
	print date.strftime("%Y-%m-%d")
	print ts.get_k_data(cfg.ShareCode, start=date.strftime("%Y-%m-%d"), end=date.strftime("%Y-%m-%d"), autype = None)
	df = ts.get_tick_data(cfg.ShareCode, date=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
	# if df is not None: # src = "tt"
	# 	print df
	# 	break
	if len(df) > 3: # src = "sn"
		SortDf = df.sort_index(ascending=False,inplace=False)#.sort_values(by = 'time', axis = 0,ascending = True)
		SortDf['Type1'] = SortDf['type'].astype('category')
		# SortDf['Type1'].cat.categories=["neu", "buy", "sel"]
		# SortDf['Type1'].cat.set_categories=["neu", "buy", "sel"]
		print SortDf['Type1']
		print len(SortDf['Type1'].cat.categories)
	time.sleep(t)
	date = date + delta
	i = i + 1
	if i == 10:
		i = 0
		time.sleep(10)
#	except:
	time.sleep(t)
	pass