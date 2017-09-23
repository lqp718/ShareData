# -*- coding: utf-8 -*-
import config as cfg
import tushare as ts
import datetime
import time
import random

date = datetime.datetime.strptime(cfg.StartDate, "%Y-%m-%d")
delta = datetime.timedelta(days=1)
i = 0

# print ts.get_hist_data(cfg.ShareCode)
while True:
	t = random.uniform(1, 5)
	try:
		print ts.get_k_data(cfg.ShareCode, start=cfg.StartDate, end=cfg.StartDate)
		df = ts.get_tick_data(cfg.ShareCode, date=date.strftime("%Y-%m-%d"), retry_count=5, pause=2, src = "tt")
		print date.strftime("%Y-%m-%d")
		if df != None:
		time.sleep(t)
		date = date + delta
		i = i + 1
		if i == 10:
			i = 0
			time.sleep(10)
	except:
		pass