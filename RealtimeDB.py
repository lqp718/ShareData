import tushare as ts
import time
import config as cfg
import json
import datetime
import logging

from pandas import DataFrame as DF
from bson.objectid import ObjectId
from pymongo import MongoClient
from error import trace_log
from Database import DB

per_price = None
per_volume = None
per_amount = None

class Realtime():
	def __init__(self, sharecode = None, output = None):
		self.StopCollect = False
		self.OutputText = output
		self.ShareDetail = DF()
		self.pre_get_df = DF()
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
		self.RealTimeDB = DB(db = "MyShare", col = sharecode + "_RT")
		self.sharecode = sharecode
		pass

	def __del__(self):
		pass

	def stop(self):
		self.StopCollect = True

	def get(self):
		df = ts.get_realtime_quotes(self.sharecode)
		for col in df.columns:
			if col in ['time', 'date', 'name', 'bid', 'ask']:
				continue
			df[col] = df[col].replace('',0)

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

			if not self.pre_get_df.equals(df):
				self.pre_get_df = df
				self.ShareDetail = self.ShareDetail.append(df, ignore_index = True)
				return df
		return None

	def GetRealTimeData(self):
		today = datetime.datetime.now().strftime('%Y-%m-%d')
		if ts.is_holiday(today):
			logging.debug("Today is not trading day, please execute this function during the share trading day")
			return 0
		while not self.StopCollect:
			t = datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M:%S'), '%H:%M:%S')
			if t <= datetime.datetime.strptime("09:25:05", '%H:%M:%S') or \
			   t >= datetime.datetime.strptime("15:00:30", '%H:%M:%S'):
				print t
				time.sleep(1)
				continue
			try:
				RTdata = self.get()
				if self.OutputText is not None:
					if RTdata is not None:
						self.OutputText.AppendText(RTdata.to_json(orient = "records"))
			except:
				pass
			time.sleep(1)
			if t >= datetime.datetime.strptime("15:00:20", '%H:%M:%S'):
				break
		self.StoreToDB()

	def StoreToDB(self):
		self.ShareDic['_id'] = ObjectId()
		self.ShareDic['high'] = self.high
		self.ShareDic['low'] = self.low
		self.ShareDic['open'] = self.open
		self.ShareDic['pre_close'] = self.pre_close
		DateStr = datetime.datetime.now().strftime('%Y-%m-%d')
		self.ShareDic['date'] = datetime.datetime.strptime(DateStr, "%Y-%m-%d")

		self.ShareDic['detail'] = json.loads(self.ShareDetail.to_json(orient = "index"))

		self.RealTimeDB.insert_one(self.ShareDic)

#Test code>>>
if __name__ == '__main__':
	RT = Realtime(sharecode = "600050")

	RT.GetRealTimeData()
	RT.StoreToDB()
#Test code<<<
