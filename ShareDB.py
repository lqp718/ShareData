# -*- coding: utf-8 -*-
import config as cfg
import tushare as ts
import datetime
import time
import random
import logging
import json
import operator

from bson.objectid import ObjectId
from error import trace_log
from Database import DB

class ShareDB():
	def __init__(self, db = "MyShare", output = None):
		self.Output = output
		self.StopOutput = False
		self._db = db
		self.RecordDB = DB(db = self._db, col = "Record")

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
				"profit": [],
				"growth": [],
				}
		basics_doc = {"CollectDate": None,
					#
					# Other key : value will be inster dynamiclly 
					#	
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

		# Record_doc = {
		# 		"type": "StockInfo",
		# 		"last_success_quarter": None,
		# }
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
				for cl in basics_clm:
					if cl not in ["timeToMarket", "name"]:
						basics_doc[cl] = df.loc[index][cl]

				tmp_basics = result[0]["basics"]
				for i in range(0, len(tmp_basics)):
					tmp_basics[i]["CollectDate"] = None
				basics_doc["CollectDate"] = None

				if basics_doc not in tmp_basics:
					basics_doc["CollectDate"] = datetime.datetime.strptime(today, "%Y-%m-%d")
					StockInfoDB.update(_filter = {"code": index}, _update = {"$push": {"basics": basics_doc}})
			time.sleep(0.2)

	def GetBasicInfomation(self, year = None, quarter = None, retry = 3):
		def template(db = None, y = None, q = None, fun = None, k = None, doc = None):
			try:
				logging.debug("Collecting %s data for %s-%s" %(k, str(y), str(q)))
				df = fun(y,q)
				for index in df.index:
					code = df.loc[index]["code"]
					i, result = db.find(_filter = {"code": code})
					if i != 0:
						doc["CollectQuarter"] = str(y) + "-" + str(q)
						selecter = "%s.CollectQuarter" % k
						i, result = db.find(_filter = {"code": code, selecter: doc["CollectQuarter"]})
						if i == 0:
							for key in doc.keys():
								if key != "CollectQuarter":
									doc[key] = df.loc[index][key]
							logging.debug ("Stock %s match, update DB" % (code))
							db.update(_filter = {"code": code}, _update = {"$push": {k: doc}})
							time.sleep(0.2)
						else:
							for key in doc.keys():
								doc[key] = None
							continue
			except:
				trace_log()
			time.sleep(random.uniform(1, 5))

		StockInfoDB = DB(db = self._db, col = "Stockinfo")
		if year == None:
			start_year = 2015
		else:
			start_year = year

		if quarter == None:
			quarter_list = [1, 2, 3, 4]
		else:
			if type(quarter) == list:
				quarter_list = quarter
			else:
				quarter_list = list(quarter)

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

		profit_doc = {"CollectQuarter": None,
					  "net_profit_ratio": None,#净利率(%)
					  "gross_profit_rate": None,#毛利率(%)
					  "business_income": None,#营业收入(百万元)
					  "bips": None,#每股主营业务收入(元)
					 }

		growth_doc = {"CollectQuarter": None,
					  "mbrg": None,#主营业务收入增长率(%)
					  "nprg": None,#净利润增长率(%)
					  "nav": None,#净资产增长率
					  "targ": None,#总资产增长率
					  "epsg": None,#每股收益增长率
					  "seg": None,#股东权益增长率
					  }
		while retry:
			while start_year <= datetime.datetime.now().year:
				for quarter in quarter_list:
					template(db = StockInfoDB, y = start_year, q = quarter, fun = ts.get_report_data, k = "report", doc = report_doc)

				for quarter in quarter_list:
					template(db = StockInfoDB, y = start_year, q = quarter, fun = ts.get_profit_data, k = "profit", doc = profit_doc)

				for quarter in quarter_list:
					template(db = StockInfoDB, y = start_year, q = quarter, fun = ts.get_growth_data, k = "growth", doc = growth_doc)

				start_year = start_year + 1

			retry = retry - 1
			if year == None:
				start_year = 2015
			else:
				start_year = year

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

		HistDataRec_doc = {
			"type": "HistoryData",
			"code": sharecode,
			"last_success": None,
			"fail_list": None
		}

		i = 0
		count = 0
		try:
			count, result = self.RecordDB.find(_filter = {"type": "HistoryData", "code": sharecode})
			if count != 0:
				date = result[0]["last_success"] + delta
			else:
				date = datetime.datetime.strptime(startdate, "%Y-%m-%d")
				#
				# Don't have the record data create one
				#
				HistDataRec_doc['last_success'] = date
				HistDataRec_doc['fail_list'] = []
				self.RecordDB.insert_one(HistDataRec_doc)
		except:
			date = datetime.datetime.strptime(startdate, "%Y-%m-%d")

		

		while not self.stop(event):
			t = random.uniform(0.5, 5)
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
					else:
						logging.debug("Get K_qfq data fail")

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
							self.RecordDB.update(_filter = {"type": "HistoryData", "code": sharecode}, _update = {"$push": {"fail_list": date}})
						for k in Share_doc.keys():
							Share_doc[k] = None
					else:
						# 获取数据失败，添加失败记录
						logging.debug("Get tick data fail")
						StockDB.insert_one(Share_doc)
						self.RecordDB.update(_filter = {"type": "HistoryData", "code": sharecode}, _update = {"$push": {"fail_list": date}})
						
				else:
					self.RecordDB.update(_filter = {"type": "HistoryData", "code": sharecode}, _update = {"$set": {"last_success": date}})
					logging.debug("No k_data, pass")
					self.OutputText("No k_data, pass" + "\n")

				time.sleep(t)
				date = date + delta

				#每收集10次数据延迟5秒
				i = i + 1
				if i == 10:
					i = 0
					time.sleep(5)
			except:
				logging.error("Exception!!!")
				trace_log()
				time.sleep(t)
				date = date + delta
			# logging.info("self.StopCollect: %s" % (self.StopCollect))
		StockDB.logout()
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

	Share = ShareDB()
	# Share.GetStockInfo()
	Share.GetBasicInfomation(year = 2015)
	# Share.GetHistoryData(sharecode = "600050", startdate = "2015-01-05")
	# print (ts.get_profit_data(2015,1))
#Test code<<<