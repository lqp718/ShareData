# -*- coding: utf-8 -*-
import re
import config as cfg
import akshare as ak
import pandas as pd
import datetime
import time
import random
import logging
import json
import operator
import csv
import os

from io import StringIO
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup, element
from bson.objectid import ObjectId
from error import trace_log
from Database import DB

class ShareDB():
	def __init__(self, db = "my_stock", output = None):
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

	def UpdateStockInfo(self, force=False):
		StockListDB = DB(db = self._db, col = "stock_list")

		if force:
			stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
			stock_zh_a_spot_em_df.to_csv("stock_zh_a_spot_em.csv", index=False)
		else:
			if os.path.exists("stock_zh_a_spot_em.csv"):
				stock_zh_a_spot_em_df = pd.read_csv("stock_zh_a_spot_em.csv", dtype={'代码': str})
			else:
				stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
				stock_zh_a_spot_em_df.to_csv("stock_zh_a_spot_em.csv", index=False)

		for doc in json.loads(stock_zh_a_spot_em_df[['代码', '名称']].to_json(orient='records')):
			i, result = StockListDB.find(_filter = {"代码": doc['代码']})
			if i == 0:
				doc["_id"] = ObjectId()
				StockListDB.insert_one(doc)

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
		def get_tick_data(csv=None, code=None, date=None, retry_count=3, pause=0.001,
		                  src='tt'):
			symbol = ct._code_to_symbol(code)
			datestr = date.replace('-', '')
			url = {
			        "tt" : ct.TICK_PRICE_URL_TT % (ct.P_TYPE['http'], ct.DOMAINS['tt'], ct.PAGES['idx'],
			                                       symbol, datestr),
			      }
			for _ in range(retry_count):
				try:
					header = {
							"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
							"Connection": "keep-alive",
							"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
							"Accept-Ancoding": "gzip, deflate",
							"Accept-Aanguage": "zh-CN,zh;q=0.9"
							}
					print(url[src])
					re = Request(url[src], headers = header)
					lines = urlopen(re, timeout=10).read()
					lines = lines.decode('GBK')
					if len(lines) < 20:
					    return None
					pd.read_table(StringIO(lines)).to_csv(csv, encoding='GBK', index=False)
					df = pd.read_table(StringIO(lines), names=ct.TICK_COLUMNS,
					                   skiprows=[0]) 
				except Exception as e:
					trace_log()
					time.sleep(pause)
				else:
				    return df
			raise IOError(ct.NETWORK_URL_ERROR_MSG)

		symbol = ct._code_to_symbol(code)
		csv_path = os.path.join("E:","ShareCSV","csv", symbol)
		if not os.path.exists(csv_path):
			os.makedirs(csv_path)
		csv_file = os.path.join(csv_path, date + "_tick.csv")
		if os.path.exists(csv_file):
			os.remove(csv_file)

		try:
			logging.debug("Get data from TT frist")
			df = get_tick_data(csv_file, code, date, retry_count, pause)
			if df is not None:
				time.sleep(random.uniform(1, 5))
				return (df)
		except:
			pass

		logging.error("Cannot get data from TT try sina")
		url_tmp = "http://market.finance.sina.com.cn/transHis.php?symbol=%s&date=%s" % (symbol, date)
		csvFile = open(csv_file,'a+',newline='', encoding='GBK')
		writer = csv.writer(csvFile)
		header = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
				"Connection": "keep-alive",
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
				"Accept-Ancoding": "gzip, deflate",
				"Accept-Aanguage": "zh-CN,zh;q=0.9"
				}
		page = 1
		while True:
			for _ in range(retry_count):
				try:
					html = None
					table = None
					url = url_tmp + "&page=%s" % (page)
					logging.debug(url)
					req = Request(url, headers = header)
					html = urlopen(req, timeout=10).read().decode('GBK')
					if html != None:
						bsObj = BeautifulSoup(html,"html.parser")
						table = bsObj.findAll("table", {"class":"datatbl"})[0] if bsObj.findAll("table", {"class":"datatbl"}) != [] else None
						if table != None:
							break
				except:
					trace_log()
				time.sleep(pause)

			if html is None:
				csvFile.close()
				raise IOError(ct.NETWORK_URL_ERROR_MSG)
			if table is None:
				break

			rows = table.findAll("tr")
			if len(rows) == 1:
				if page == 1 and url_tmp.startswith("http://market"):
					logging.debug("can't get tick data from http://market.finance.sina.com.cn try http://vip.stock.finance.sina.com.cn")
					url_tmp = "http://vip.stock.finance.sina.com.cn/quotes_service/view/vMS_tradehistory.php?symbol=%s&date=%s" % (symbol, date)
					continue
				else:
					break
			elif len(rows) == 2:
				row = rows[1]
				if list(filter(lambda x: x.get_text() == "该股票没有交易数据", row.findAll(['td','th']))):
					break
			try:
				for row in rows:
					csvRow = []
					for cell in row.findAll(['td','th']):
						text = cell.get_text()
						if text in ["-100.00%"]:
							csvRow = []
							break
						if page == 1:
							if text not in ["涨跌幅"]:
								if "%" not in text:
									csvRow.append(text.replace(",", ""))
						else:
							if text not in ["成交时间", "成交价", "涨跌幅", "价格变动", "成交量(手)", "成交额(元)", "性质"]:
								if "%" not in text:
									csvRow.append(text.replace(",", ""))
					if csvRow:
						writer.writerow(csvRow)
			except:
				logging.error("write csv fail")
				trace_log()
			page = page + 1
			time.sleep(random.uniform(1, 3))

		csvFile.close()
		df = pd.read_csv(csv_file, names = ['time', 'price', 'change', 'volume', 'amount', 'type'],
		                   skiprows=[0], encoding = "GBK")
		return (df)

	def GetHistoryData(self, stock = "", start_date = "", event = None):
		delta = datetime.timedelta(days=1)
		StockDB = DB(db = self._db, col = stock)
		logging.info("Getting historyData for %s" % (stock))

		stock_doc = {
		"_id": None,
		"date": None,
		"k_data": None,
		"k_data_qfq": None,
		"k_data_hfq": None,
		"tick": None
		}

		HistDataRec_doc = {
			"type": "Record",
			"last_success": None,
			"fail_list": None
		}

		count = 0
		try:
			count, result = StockDB.find(_filter = {"type": "Record"})
			if count != 0:
				date = result[0]["last_success"] + delta
			else:
				date = datetime.datetime.strptime(start_date, "%Y%m%d")
				#
				# Don't have the record data create one
				#
				HistDataRec_doc['last_success'] = date - delta
				HistDataRec_doc['fail_list'] = []
				StockDB.insert_one(HistDataRec_doc)
		except:
			date = datetime.datetime.strptime(start_date, "%Y%m%d")

		logging.debug("last_success date is %s" % (date))
		if date.strftime("%Y%m%d") >= datetime.datetime.today().strftime("%Y%m%d"):
			logging.info("All the share data were collected, exit the collection progress!")
			return 0

		today = datetime.datetime.today().strftime("%Y%m%d")
		k_df = ak.stock_zh_a_hist(symbol=stock, period='daily', start_date=date.strftime("%Y%m%d"), end_date=today)

		k_df.sort_values(["日期"], inplace=True, ignore_index=True)

		k_qfq_df = ak.stock_zh_a_hist(symbol=stock, period='daily', start_date=date.strftime("%Y%m%d"), end_date=today, adjust='qfq')
		k_hfq_df = ak.stock_zh_a_hist(symbol=stock, period='daily', start_date=date.strftime("%Y%m%d"), end_date=today, adjust='hfq')

		k_df_array = json.loads(k_df.to_json(index=False, orient="records"))

		for record in k_df_array:
			try:
				stock_doc['_id'] = ObjectId()
				stock_doc['date'] = datetime.datetime.utcfromtimestamp(record['日期'] / 1000).date()
				del record['日期']
				del record['股票代码']
				stock_doc['k_data'] = record

				k_qfq_date_df = k_qfq_df[k_qfq_df["日期"] == stock_doc['date']]
				if k_qfq_date_df.empty:
					logging.warning(f"Cannot get qfq k data for {stock} in {stock_doc['date']}")
				else:
					k_data_qfq = json.loads(k_qfq_date_df.to_json(index=False, orient="records"))
					del k_data_qfq['日期']
					del k_data_qfq['股票代码']
					stock_doc['k_data_qfq'] = k_data_qfq


				k_hfq_date_df = k_hfq_df[k_hfq_df["日期"] == stock_doc['date']]
				if k_hfq_date_df.empty:
					logging.warning(f"Cannot get hfq k data for {stock} in {stock_doc['date']}")
				else:
					k_data_hfq = json.loads(k_hfq_date_df.to_json(index=False, orient="records"))
					del k_data_hfq['日期']
					del k_data_qfq['股票代码']
					stock_doc['k_data_hfq'] = k_data_hfq

				StockDB.insert_one(stock_doc)
				StockDB.update(_filter = {"type": "Record"}, _update = {"$set": {"last_success": stock_doc['date']}})
			except:
				logging.error("Exception!!! GetHistoryData fail")
				trace_log()

			break
		return 0


#Test code >>>
if __name__ == '__main__':
	log_file = "ShareDB.log"
	logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        filename=log_file)
	console_logger = logging.StreamHandler()
	console_logger.setLevel(logging.INFO)
	console_logger.setFormatter(logging.Formatter("%(message)s"))
	logging.getLogger().addHandler(console_logger)

	# stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="")
	# print(stock_zh_a_hist_df)

	Share = ShareDB()
	Share.GetHistoryData(stock='000001', start_date='20150101')

	# Share.Get_Tick_Data("000012", date="2018-07-18", retry_count=3, pause=4)
	# Share.GetStockInfo()
	# Share.GetBasicInfomation(year = 2015)
	# for i in Share.GetHistoryData(sharecode = "600050", startdate = "2015-01-05"):
	# 	pass
	# qfq_df = ts.get_k_data("603713", start="2015-01-05", autype = None, retry_count=10, pause=4)
	# print (qfq_df)
	# if qfq_df is not None and len(qfq_df) != 0:
	# 	df = qfq_df.loc[qfq_df["date"] == "2015-01-05"]
	# 	print (df)
	# 	if df is not None and len(df) != 0:
	# 		print(json.loads(df.to_json(orient = "records"))[0])

	# df = ts.get_k_data("600145", start = "2018-01-05", autype = None, retry_count=10, pause=4)
	# print (ts.get_profit_data(2015,1))
#Test code<<<