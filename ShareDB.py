# -*- coding: utf-8 -*-
import config as cfg
import tushare as ts
import datetime
import time
import random
import logging
import json
import pandas

from pymongo import MongoClient
from error import trace_log

if __name__ == '__main__':

	log_file = "ShareDB.log"
	logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        filename=log_file)
	console_logger = logging.StreamHandler()
	console_logger.setLevel(logging.DEBUG)
	console_logger.setFormatter(logging.Formatter("%(message)s"))
	logging.getLogger().addHandler(console_logger)

	date = datetime.datetime.strptime(cfg.StartDate, "%Y-%m-%d")
	delta = datetime.timedelta(days=1)
	i = 0

	dic = {
	"date": "XXXX-XX-XX",
	"k_data": None,
	"tick": None
	}

	conn = MongoClient()
	db = conn.MyShare
	Collection = db.Tmp

	while True:
		t = random.uniform(1, 5)
		try:
			dic['date'] = date.strftime("%Y-%m-%d")
			df = ts.get_k_data(cfg.ShareCode, start=date.strftime("%Y-%m-%d"), end=date.strftime("%Y-%m-%d"), autype = None)
			del df['code']
			del df['date']
			dic['k_data'] = json.loads(df.to_json(orient = "records"))[0]
			df = ts.get_tick_data(cfg.ShareCode, date=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
			if len(df) > 3: # src = "sn"
				SortDf = df.sort_values(by = 'time', axis = 0, ascending = True)#.sort_index(ascending=False,inplace=False)
				SortDf.reset_index(drop = True, inplace = True)
				SortDf['type'] = SortDf['type'].replace("买盘", 1).replace("卖盘", -1).replace("中性盘", 0)
				SortDf['change'] = SortDf['change'].replace('--', '0').astype('float')
				dic['tick'] = json.loads(SortDf.to_json(orient = "index"))
				Collection.insert_one(dic)

			if date.strftime("%Y-%m-%d") == datetime.datetime.now().strftime('%Y-%m-%d'):
				break
			time.sleep(t)
			date = date + delta
			i = i + 1
			if i == 10:
				i = 0
				time.sleep(10)
		except:
			logging.error(date.strftime("%Y-%m-%d") + "\n")
			trace_log()
			time.sleep(t)
			date = date + delta

	Collection.rename(cfg.ShareCode)