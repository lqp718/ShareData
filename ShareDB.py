# -*- coding: utf-8 -*-
import config as cfg
import tushare as ts
import pandas as pd
import datetime
import time
import random
import logging
import json
import operator
import csv
import os

from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from error import trace_log
from Database import DB
from tushare.stock import cons as ct

class ShareDB():
	def __init__(self, db = "MyShare", output = None):
		self.Output = output
		self.StopOutput = False
		self._db = db
		self.RecordDB = DB(db = self._db, col = "Record")
		self.TradeDayList = None

	def isTradeDay(self, date):
		if self.TradeDayList == None:
			df = pd.read_csv("calAll.csv")
			self.TradeDayList = df.loc[df["isOpen"] == 1]["calendarDate"].tolist()

		if date in self.TradeDayList:
			return True
		else:
			return False


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
				time.sleep(0.2)
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

	def Get_Tick_Data(self, code=None, date=None, retry_count=3, pause=0.001):
		symbol = ct._code_to_symbol(code)
		url_tmp = "http://market.finance.sina.com.cn/transHis.php?symbol=%s&date=%s" % (symbol, date)
		csn_path = os.path.join("csv", symbol)
		if not os.path.exists(csn_path):
			os.makedirs(csn_path)
		csv_file = os.path.join(csn_path, date + "_tick.csv")
		if os.path.exists(csv_file):
			os.remove(csv_file)

		csvFile = open(csv_file,'a+',newline='', encoding='GBK')
		writer = csv.writer(csvFile)
		header = {"Host": "market.finance.sina.com.cn",
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
				"Connection": "keep-alive",
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
				"Accept-Ancoding": "gzip, deflate",
				"Accept-Aanguage": "zh-CN,zh;q=0.9"
				}

		for index in range (1, 150):
			for _ in range(retry_count):
				try:
					html = None
					url = url_tmp + "&page=%s" % (index)
					logging.debug(url)
					req = Request(url, headers = header)
					html = urlopen(req, timeout=10).read().decode('GBK')
					if html != None:
						break
				except:
					trace_log()
					time.sleep(pause)

			if html is None:
				csvFile.close()
				raise IOError(ct.NETWORK_URL_ERROR_MSG)

			bsObj = BeautifulSoup(html,"html.parser")
			table = bsObj.findAll("table")[0]
			if table is None:
				break
			rows = table.findAll("tr")
			if len(rows) == 1:
				break
			try:
				for row in rows:
					csvRow = []
					for cell in row.findAll(['td','th']):
						text = cell.get_text()
						if index == 1:
							csvRow.append(text.replace(",", ""))
						else:
							if text not in ["成交时间", "成交价", "价格变动", "成交量(手)", "成交额(元)", "性质"]:
								csvRow.append(text.replace(",", ""))
					if csvRow:
						writer.writerow(csvRow)
			except:
				pass
			time.sleep(1)

		csvFile.close()
		df = pd.read_csv("editors.csv", names = ['time', 'price', 'change', 'volume', 'amount', 'type'],
		                   skiprows=[0], encoding = "GBK")
		return (df)

	def GetHistoryData(self, sharecode = None, startdate = None, event = None):
		delta = datetime.timedelta(days=1)
		StockDB = DB(db = "MyShare_Test", col = sharecode)
		logging.info("Getting historyData for %s" % (sharecode))

		Share_doc = {
		"_id": None,
		"date": None,
		"k_data": None,
		"tick": None
		}

		HistDataRec_doc = {
			"type": "Record",
			"last_success": None,
			"fail_list": None
		}

		# i = 0
		count = 0
		try:
			count, result = StockDB.find(_filter = {"type": "Record"})
			if count != 0:
				date = result[0]["last_success"] + delta
			else:
				date = datetime.datetime.strptime(startdate, "%Y-%m-%d")
				#
				# Don't have the record data create one
				#
				HistDataRec_doc['last_success'] = date
				HistDataRec_doc['fail_list'] = []
				StockDB.insert_one(HistDataRec_doc)
		except:
			date = datetime.datetime.strptime(startdate, "%Y-%m-%d")

		for _ in range(3):
			k_df = None
			try:
				k_df = ts.get_k_data(sharecode, start=date.strftime("%Y-%m-%d"), autype = None, retry_count=10, pause=4)
			except:
				logging.error("Exception!!! get_k_data fail")
				trace_log()
				yield 1
			if k_df is not None and len(k_df) != 0:
				break
			time.sleep(random.uniform(1, 5))

		if k_df is None or len(k_df) == 0:
			base = date
			days = (datetime.datetime.now() - date).days
			date_list = [base + datetime.timedelta(days=x) for x in range(0, days + 1)]
			for day in date_list:
				if self.isTradeDay(day.strftime('%Y-%m-%d')):
					logging.error("！！！k_df is None, skip this stock")
					break
			return 0

		while not self.stop(event):
			if date.strftime("%Y-%m-%d") >= datetime.datetime.today().strftime("%Y-%m-%d"):
				logging.info("All the share data were collected, exit the collection progress!")
				break
			try:
				Share_doc['date'] = date
				logging.info(Share_doc['date'])
				df = k_df.loc[k_df["date"] == date.strftime("%Y-%m-%d")]

				if df is not None and len(df) != 0:
					logging.debug("Get K data successful")
					Share_doc['_id'] = ObjectId()
					Share_doc['k_data'] = json.loads(df.to_json(orient = "records"))[0]

					#获取复权数据
					# time.sleep(random.uniform(1, 10))
					# qfq_df = ts.get_k_data(sharecode, start=date.strftime("%Y-%m-%d"), end=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
					# if qfq_df is not None and len(qfq_df) != 0:
					# 	Share_doc['k_data_qfq'] = json.loads(qfq_df.to_json(orient = "records"))[0]
					# else:
					# 	logging.debug("Get K_qfq data fail")

					#获取历史分笔数据
					df = self.Get_Tick_Data(sharecode, date=date.strftime("%Y-%m-%d"), retry_count=3, pause=4)
					if len(df) > 3: # src = "sn"
						logging.debug("Getting tick data successful")
						SortDf = df.sort_values(by = 'time', axis = 0, ascending = True)#.sort_index(ascending=False,inplace=False)
						SortDf.reset_index(drop = True, inplace = True)
						SortDf['type'] = SortDf['type'].replace("买盘", 1).replace("卖盘", -1).replace("中性盘", 0)
						SortDf['change'] = SortDf['change'].replace('--', '0').astype('float')
						Share_doc['tick'] = json.loads(SortDf.to_json(orient = "index"))

						#将获取到的数据插入数据库
						InsertResult = StockDB.insert_one(Share_doc)
						if InsertResult.acknowledged:
							StockDB.update(_filter = {"type": "Record"}, _update = {"$set": {"last_success": date}})
							logging.debug("Insert data successful ObjectId = %s" %(InsertResult.inserted_id))
						else:
							logging.error("Insert data to DB fail")
							StockDB.update(_filter = {"type": "Record"}, _update = {"$push": {"fail_list": date}})
						for k in Share_doc.keys():
							Share_doc[k] = None
					else:
						# 获取数据失败，添加失败记录
						logging.error("Getting tick data fail")
						StockDB.insert_one(Share_doc)
						StockDB.update(_filter = {"type": "Record"}, _update = {"$push": {"fail_list": date}})
						
				else:
					StockDB.update(_filter = {"type": "Record"}, _update = {"$set": {"last_success": date}})
					logging.info("No k_data, pass")

				# time.sleep(random.uniform(1, 5))
				date = date + delta

				#每收集10次数据延迟5秒
				# i = i + 1
				# if i == 10:
				# 	i = 0
				# 	time.sleep(10)
			except:
				logging.error("Exception!!! Get_Tick_Data fail")
				trace_log()
				yield 1
		StockDB.logout()
		return 0


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
	# Share.GetBasicInfomation(year = 2015)
	# Share.GetHistoryData(sharecode = "600050", startdate = "2015-01-05")
	# qfq_df = ts.get_k_data("603713", start="2015-01-05", autype = None, retry_count=10, pause=4)
	# print (qfq_df)
	# if qfq_df is not None and len(qfq_df) != 0:
	# 	df = qfq_df.loc[qfq_df["date"] == "2015-01-05"]
	# 	print (df)
	# 	if df is not None and len(df) != 0:
	# 		print(json.loads(df.to_json(orient = "records"))[0])

	df = ts.get_k_data("600050", start = "2015-01-05", autype = None, retry_count=10, pause=4)
	print (df)
	# print (ts.get_profit_data(2015,1))
#Test code<<<