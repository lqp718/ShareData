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
	def __init__(self, db = "MyShare", output = None):
		self.Output = output
		self.StopOutput = False
<<<<<<< HEAD
		self._db = db
		self.RecordDB = DB(db = self._db, col = "Record")
=======
		self.ShareCode = sharecode
		self.StartDate = startdate
		self.ShareDB = DB(db = "MyShare", col = sharecode)
		self.RecordDB = DB(db = "MyShare", col = "Record")
		self.StockInfoDB = DB(db = "MyShare", col = "Stockinfo")
>>>>>>> 7d7caaef0ad4bf4946499109c5234668d1eaf788

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

	def GetStockInfo(self):
		StockInfoDB = DB(db = self._db, col = "Stockinfo")
		doc = { "_id" : None,
				"code" : None,
				"name" : None,
				"timeToMarket": None,
				"basics": [],
				"report": [],
				"growth": [],
				"profit": [],
				}
		basics_doc = {"CollectDate": None,
					#
					# Other key : value will be inster dynamiclly 
					#	
				}

		report_doc = {"CollectQuarter": None,
					  "eps": None,#每股收益
					  "eps_yoy": None,#每股收益同比(%)
					  "bvps": None,#每股净资产
					  "roe": None,#净资产收益率(%)
					  "epcf": None,#每股现金流量(元)
					  "net_profits": None,#净利润(万元)
					  "profits_yoy": None,#净利润同比(%)
					  "distrib": None,#分配方案
					  "report_date": None,#发布日期
					  }

		growth_doc = {"CollectQuarter": None,
					  "mbrg": None,#主营业务收入增长率(%)
					  "nprg": None,#净利润增长率(%)
					  "nav": None,#净资产增长率
					  "targ": None,#总资产增长率
					  "epsg": None,#每股收益增长率
					  "seg": None,#股东权益增长率
					  }

		profit_doc = {"CollectQuarter": None,
					  "net_profit_ratio": None,#净利率(%)
					  "gross_profit_rate": None,#毛利率(%)
					  "business_income": None,#营业收入(百万元)
					  "bips": None,#每股主营业务收入(元)
					 }

		df = ts.get_stock_basics()
		basics_clm = [ "name",#股票名称
				"pe", #市盈率
				"outstanding",#流通股本(亿)
				"totals",#总股本(亿)
				"totalAssets",#总资产(万)
				"liquidAssets",#流动资产
				"fixedAssets",#固定资产
				"reserved",#公积金
				"reservedPerShare",#每股公积金
				"esp",#每股收益
				"bvps",#每股净资
				"pb",#市净率
				"timeToMarket",#上市日期
				"undp",#未分利润
				"perundp",#每股未分配
				"rev",#收入同比(%)
				"profit",#利润同比(%)
				"gpr",#毛利率(%)
				"npr",#净利润率(%)
				"holders"#股东人数
				]
		Record_doc = {

		}
		for index in df.index:
			i, result = StockInfoDB.find(_filter = {"code": index})
			if i == 0:
				doc["code"] = str(index)
				doc["_id"] = ObjectId()
				today = datetime.datetime.now().strftime('%Y-%m-%d')
				basics_doc["CollectDate"] = datetime.datetime.strptime(today, "%Y-%m-%d")
				for cl in basics_clm:
					if cl == "timeToMarket":
						try:
							doc["timeToMarket"] = datetime.datetime.strptime(str(df.loc[index]["timeToMarket"]), "%Y%m%d")
						except:
							break
					elif cl == "name":
						doc["name"] = df.loc[index]["name"]
					else:
						basics_doc[cl] = df.loc[index][cl]
				doc["basics"] = []
				doc["basics"].append(basics_doc)
				StockInfoDB.insert_one(doc)
			else:
				today = datetime.datetime.now().strftime('%Y-%m-%d')
				basics_doc["CollectDate"] = None
				for cl in basics_clm:
					if cl not in ["timeToMarket", "name"]:
						basics_doc[cl] = df.loc[index][cl]

				tmp_basics = result[0]["basics"]
				for i in range(0, len(tmp_basics)):
					tmp_basics[i]["CollectDate"] = None

				if basics_doc not in tmp_basics:
					basics_doc["CollectDate"] = datetime.datetime.strptime(today, "%Y-%m-%d")
					StockInfoDB.update(_filter = {"code": index}, _update = {"$push": {"basics": basics_doc}})
			time.sleep(0.1)
			break

		year = 2015
		quarter_list = [1, 2, 3, 4]
		while year <= datetime.datetime.now().year:
			for quarter in quarter_list:
				#try:
					df = ts.get_report_data(year,quarter)
					report_doc["CollectQuarter"] = str(year) + "-" + str(quarter)
					print report_doc["CollectQuarter"]
					for index in df.index:
						code = df.loc[index]["code"]
						print code
						i, result = StockInfoDB.find(_filter = {"code": code})
						if i != 0:
							for key in report_doc.keys():
								if key != "CollectQuarter":
									report_doc[key] = df.loc[index][key]
							StockInfoDB.update(_filter = {"code": code}, _update = {"$push": {"report": report_doc}})
						else:
							continue
				#except:
					#pass
					break
			break
			year = year + 1


	def GetHistoryData(self, sharecode = None, startdate = None, event = None):
		delta = datetime.timedelta(days=1)
		StockDB = DB(db = "MyShare", col = sharecode)

		Share_doc = {
		"_id": None,
		"date": None,
		"k_data": None,
		"k_data_qfq": None,
		"tick": None
		}

<<<<<<< HEAD
		HistDataRec_doc = {
			"type": "HistoryData",
			"code": sharecode,
			"last_success": None,
			"fail_list": None
=======
		Record_doc = {
			"code": self.ShareCode,
			"success": None,
			"fail" : []
>>>>>>> 7d7caaef0ad4bf4946499109c5234668d1eaf788
		}

		i = 0
		count = 0
		record = []
		try:
<<<<<<< HEAD
			count, result = self.RecordDB.find(_filter = {"type": "HistoryData", "code": sharecode})
			if count != 0:
				date = result[0]["last_success"] + delta
=======
			count, record = self.RecordDB.find(_filter = {"code": self.ShareCode})
			if count != 0:
				date = record[0]["success"] + delta
>>>>>>> 7d7caaef0ad4bf4946499109c5234668d1eaf788
			else:
				date = datetime.datetime.strptime(startdate, "%Y-%m-%d")
				#
				# Don't have the record data create one
				#
<<<<<<< HEAD
				HistDataRec_doc['last_success'] = date
				HistDataRec_doc['fail_list'] = []
				self.RecordDB.insert_one(HistDataRec_doc)
=======
				Record_doc['success'] = None
				self.RecordDB.insert_one(Record_doc)
>>>>>>> 7d7caaef0ad4bf4946499109c5234668d1eaf788
		except:
			date = datetime.datetime.strptime(startdate, "%Y-%m-%d")

		

		while not self.stop(event):
			t = random.uniform(1, 10)
			if date > datetime.datetime.now():
				logging.info("All the share data were collected, exit the collection progress!")
				break
			try:
				Share_doc['date'] = date
				logging.debug(Share_doc['date'])
				self.OutputText("Collecting Share data for" + Share_doc['date'].strftime("%Y-%m-%d") + "\n")
				df = ts.get_k_data(sharecode, start=date.strftime("%Y-%m-%d"), end=date.strftime("%Y-%m-%d"), autype = None, retry_count=10, pause=4)
				if df is not None and len(df) != 0:
					Share_doc['_id'] = ObjectId()
					Share_doc['k_data'] = json.loads(df.to_json(orient = "records"))[0]

					#获取复权数据
					time.sleep(t)
					qfq_df = ts.get_k_data(sharecode, start=date.strftime("%Y-%m-%d"), end=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
					if qfq_df is not None and len(qfq_df) != 0:
						Share_doc['k_data_qfq'] = json.loads(qfq_df.to_json(orient = "records"))[0]

					#获取历史分笔数据
					df = ts.get_tick_data(sharecode, date=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
					if len(df) > 3: # src = "sn"
						SortDf = df.sort_values(by = 'time', axis = 0, ascending = True)#.sort_index(ascending=False,inplace=False)
						SortDf.reset_index(drop = True, inplace = True)
						SortDf['type'] = SortDf['type'].replace("买盘", 1).replace("卖盘", -1).replace("中性盘", 0)
						SortDf['change'] = SortDf['change'].replace('--', '0').astype('float')
						Share_doc['tick'] = json.loads(SortDf.to_json(orient = "index"))

						#将获取到的数据插入数据库
						InsertResult = StockDB.insert_one(Share_doc)
						if InsertResult.acknowledged:
							self.RecordDB.update(_filter = {"type": "HistoryData", "code": sharecode}, _update = {"$set": {"last_success": date}})
							logging.debug("Insert data successful ObjectId = %s" %(InsertResult.inserted_id))
							self.OutputText("Collect data successful and insert to database ObjectId = %s" %(InsertResult.inserted_id) + "\n")
						else:
							logging.debug("Insert data fail")
<<<<<<< HEAD
							self.RecordDB.update(_filter = {"type": "HistoryData", "code": sharecode}, _update = {"$push": {"fail_list": date}})
					else:
						# 获取数据失败，添加失败记录
						self.RecordDB.update(_filter = {"type": "HistoryData", "code": sharecode}, _update = {"$push": {"fail_list": date}})
						
				else:
					self.RecordDB.update(_filter = {"type": "HistoryData", "code": sharecode}, _update = {"$set": {"last_success": date}})
=======
					else:
						fail = record[0]["fail"]
						fail.append(date)
						self.RecordDB.update(_filter = {"code": self.ShareCode}, _update = {"$set": {"fail": fail}})
						
				else:
					self.RecordDB.update(_filter = {"code": self.ShareCode}, _update = {"$set": {"success": date}})
>>>>>>> 7d7caaef0ad4bf4946499109c5234668d1eaf788
					logging.debug("No k_data, pass")
					self.OutputText("No k_data, pass" + "\n")

				time.sleep(t)
				date = date + delta

				#每收集10次数据延迟10秒
				i = i + 1
				if i == 10:
					i = 0
					time.sleep(10)
			except:
				logging.error("Exception!!!")
				trace_log()
				time.sleep(t)
				date = date + delta
<<<<<<< HEAD
			# logging.info("self.StopCollect: %s" % (self.StopCollect))
		StockDB.logout()
=======
		self.ShareDB.logout()
>>>>>>> 7d7caaef0ad4bf4946499109c5234668d1eaf788
		self.RecordDB.logout()


#Test code >>>
if __name__ == '__main__':
<<<<<<< HEAD
	log_file = "ShareDB.log"
	logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        filename=log_file)
	console_logger = logging.StreamHandler()
	console_logger.setLevel(logging.DEBUG)
	console_logger.setFormatter(logging.Formatter("%(message)s"))
	logging.getLogger().addHandler(console_logger)

	Share = ShareDB()
	Share.GetStockInfo()
	# Share.GetHistoryData(sharecode = "000001", startdate = "2015-01-05")
	# print ts.get_k_data("600050", start="2015-01-05", autype=None, retry_count=10, pause=4)
	#print ts.get_report_data(2018,2)["code"]
=======
	# log_file = "ShareDB.log"
	# logging.basicConfig(
 #        level=logging.DEBUG,
 #        format="%(message)s",
 #        filename=log_file)
	# console_logger = logging.StreamHandler()
	# console_logger.setLevel(logging.DEBUG)
	# console_logger.setFormatter(logging.Formatter("%(message)s"))
	# logging.getLogger().addHandler(console_logger)

	# Share = ShareDB(sharecode = "601901", startdate = "2016-01-13")
	# Share.GetStockInfo()
	print (ts.get_profit_data(2015,1))
>>>>>>> 7d7caaef0ad4bf4946499109c5234668d1eaf788
#Test code<<<