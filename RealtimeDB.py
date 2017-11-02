import tushare as ts
import time
import config as cfg
import json
import datetime

from pandas import DataFrame as df
from bson.objectid import ObjectId
from pymongo import MongoClient
from error import trace_log

per_price = None
per_volume = None
per_amount = None

class Realtime():
	def __init__(self):
		self.ShareDetail = df()
		self.high = 0
		self.low = 0
		self.open = 0
		self.pre_close = 0
		self.ShareDic = {
			"_id": None,
			"date": "XXXX-XX-XX",
			"open": None,
			"pre_close": None,
			"high": None,
			"low": None,
			"detail": None
		}
		pass

	def __del__(self):
		pass

	def get(self):
		df = ts.get_realtime_quotes(cfg.ShareCode)
		if df is not None:

			if self.open != df['open'].astype('float').values[0]:
				self.open = df['open'].astype('float').values[0]

			if self.pre_close != df['pre_close'].astype('float').values[0]:
				self.pre_close = df['pre_close'].astype('float').values[0]

			if self.high != df['high'].astype('float').values[0]:
				self.high = df['high'].astype('float').values[0]

			if self.low != df['low'].astype('float').values[0]:
				self.low = df['low'].astype('float').values[0]

			vls = [cls for cls in df.columns if '_v' in cls]
			pls = [cls for cls in df.columns if '_p' in cls]

			df = df.loc[:,['time'] + ['price'] + vls + pls]
			for col in df.columns:
				if col == 'time':
					continue
				df[col] = df[col].astype('float')

			if self.ShareDetail.empty:
				self.ShareDetail = self.ShareDetail.append(df, ignore_index = True)
			else:
				tail = self.ShareDetail.tail(1).reset_index(drop = True)
				if not tail.equals(df):
					self.ShareDetail = self.ShareDetail.append(df, ignore_index = True)

	def StoreToDB(self):
		conn = MongoClient()
		db = conn.MyShare
		Collection = db.get_collection(name = cfg.ShareCode + "_RT")
		if Collection is None:
			Collection = db.create_collection(name = cfg.ShareCode + "_RT")
		pass

		self.ShareDic['_id'] = ObjectId()
		self.ShareDic['high'] = self.high
		self.ShareDic['low'] = self.low
		self.ShareDic['open'] = self.open
		self.ShareDic['pre_close'] = self.pre_close
		self.ShareDic['date'] = datetime.datetime.now().strftime('%Y-%m-%d')

		self.ShareDic['detail'] = json.loads(self.ShareDetail.to_json(orient = "index"))

		Collection.insert_one(self.ShareDic)

#Test code>>>
if __name__ == '__main__':
	RT = Realtime()
	i = 0
	while True:
		if datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M:%S'), '%H:%M:%S') <= datetime.datetime.strptime("09:25:00", '%H:%M:%S'):
			time.sleep(1)
			continue
		RT.get()
		time.sleep(1)
		if datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M:%S'), '%H:%M:%S') >= datetime.datetime.strptime("15:00:30", '%H:%M:%S'):
			break

	RT.StoreToDB()
#Test code<<<
