# -*- coding: utf-8 -*-
import config as cfg
import tushare as ts
import datetime
import time
import random
import logging
import json

from bson.objectid import ObjectId
from error import trace_log
from Database import DB

class ShareDB():
	def __init__(self, sharecode = None, startdate = None, output = None):
		self.Output = output
		self.StopOutput = False
		self.ShareCode = sharecode
		self.StartDate = startdate
		self.ShareDB = DB(db = "MyShare", col = sharecode)
		self.RecordDB = DB(db = "MyShare", col = "LastRecord")

	def OutputText(self, s):
		if self.StopOutput:
			return 0
		if self.Output is not None:
			self.Output.AppendText(s)

	def stop(self, event):
		if event is None:
			return False
		else:
			if event.isSet():
				return False
			else:
				self.StopOutput = True
				return True


	def GetHistoryData(self, event = None):
		delta = datetime.timedelta(days=1)

		Share_dic = {
		"_id": None,
		"date": None,
		"k_data": None,
		"tick": None
		}

		Record_dic = {
			"code": self.ShareCode,
			"date": None,
		}

		i = 0
		count = 0
		try:
			count, result = self.RecordDB.find(_filter = {"code": self.ShareCode})
			if count != 0:
				date = result[0]["date"] + delta
			else:
				date = datetime.datetime.strptime(self.StartDate, "%Y-%m-%d")
				#
				# Don't have the record data create one
				#
				Record_dic['date'] = date
				self.RecordDB.insert_one(Record_dic)
		except:
			date = datetime.datetime.strptime(self.StartDate, "%Y-%m-%d")

		

		while not self.stop(event):
			t = random.uniform(1, 5)
			if date > datetime.datetime.now():
				logging.info("All the share data were collected, exit the collection progress!")
				break
			try:
				Share_dic['date'] = date
				logging.debug(Share_dic['date'])
				self.OutputText("Collecting Share data for" + Share_dic['date'].strftime("%Y-%m-%d") + "\n")
				df = ts.get_hist_data(self.ShareCode, start=date.strftime("%Y-%m-%d"), end=date.strftime("%Y-%m-%d"))
				if df is not None and len(df) != 0:
					Share_dic['_id'] = ObjectId()
					Share_dic['k_data'] = json.loads(df.to_json(orient = "records"))[0]
					df = ts.get_tick_data(self.ShareCode, date=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
					if len(df) > 3: # src = "sn"
						SortDf = df.sort_values(by = 'time', axis = 0, ascending = True)#.sort_index(ascending=False,inplace=False)
						SortDf.reset_index(drop = True, inplace = True)
						SortDf['type'] = SortDf['type'].replace("买盘", 1).replace("卖盘", -1).replace("中性盘", 0)
						SortDf['change'] = SortDf['change'].replace('--', '0').astype('float')
						Share_dic['tick'] = json.loads(SortDf.to_json(orient = "index"))
						InsertResult = self.ShareDB.insert_one(Share_dic)
						if InsertResult.acknowledged:
							self.RecordDB.update(_filter = {"code": self.ShareCode}, _update = {"$set": {"date": date}})
							logging.debug("Insert data successful ObjectId = %s" %(InsertResult.inserted_id))
							self.OutputText("Collect data successful and insert to database ObjectId = %s" %(InsertResult.inserted_id) + "\n")
						else:
							logging.debug("Insert data fail")
						
				else:
					self.RecordDB.update(_filter = {"code": self.ShareCode}, _update = {"$set": {"date": date}})
					logging.debug("No k_data, pass")
					self.OutputText("No k_data, pass" + "\n")

				time.sleep(t)
				date = date + delta
				i = i + 1
				if i == 10:
					i = 0
					time.sleep(10)
			except:
				logging.error("Exception!!!")
				trace_log()
				time.sleep(t)
				date = date + delta
			# logging.info("self.StopCollect: %s" % (self.StopCollect))
		self.ShareDB.logout()
		self.RecordDB.logout()


#Test code >>>
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

	Share = ShareDB(sharecode = "601901", startdate = "2016-01-13")
	Share.GetHistoryData()
#Test code<<<