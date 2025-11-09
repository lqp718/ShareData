# import wx  
# # -*- coding: utf-8 -*-
# import config as cfg
# import tushare as ts
# import datetime
# import time
# import random
# import logging
# import json

# from bson.objectid import ObjectId
# from error import trace_log
# from Database import DB

# class Frame1(wx.Frame):
#     def __init__(self,parent):
#         wx.Frame.__init__(self, parent=parent, style = wx.CAPTION | wx.SIMPLE_BORDER | wx.MINIMIZE_BOX | wx.CLOSE_BOX, \
#             title='TuShare Strategy system',size=(1380,800))

# 	def GetHistoryData(self, event = None):
# 		delta = datetime.timedelta(days=1)
# 		date = "2014-01-09"
# 		while True:
# 			df = ts.get_tick_data(self.ShareCode, date=date.strftime("%Y-%m-%d"), retry_count=10, pause=4)
# 			self.ShareDB.insert_one(df)
# 			date = date + delta

# if __name__ == '__main__':
#     app = wx.App()
#     frame = Frame1(None)
#     frame.Show()
#     app.MainLoop()

# import tushare as ts

# # # print (ts.get_hist_data(code = "601901", start = "2015-01-05"))
# # # print (ts.get_tick_data(code = "600848", date = "2015-01-05"))
# # print (ts.get_stock_basics())
# #print ts.get_hist_data(code = "600050", start = "2015-01-01")
# for i in ts.get_report_data(2016,1)["code"]:
#     print (i)

# import socks
# import socket
# import time
# from urllib.request import urlopen
# import urllib
# import random
# import datetime

# proxy_support = urllib.request.ProxyHandler({'http': '219.141.153.10:80'})
# opener = urllib.request.build_opener(proxy_support)
# urllib.request.install_opener(opener)
# # lines = urlopen("http://http.tiqu.qingjuhe.cn/getip?num=3&type=1&pro=&city=0&yys=0&port=1&pack=19139&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=0&regions=").read().decode('utf-8')
# # print ("您的套餐今日已到达上限" in lines)
# print (urlopen("http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?").read().decode('GBK'))
# # #"http://market.finance.sina.com.cn/transHis.php?"
# print (urlopen("http://market.finance.sina.com.cn/transHis.php?").read().decode('GBK'))
# print (urlopen("http://icanhazip.com/").read().decode('GBK'))
# "http://http.tiqu.qingjuhe.cn/getip?num=1&type=1&pro=&city=0&yys=0&port=1&pack=19139&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=0&regions="
# "http://http.tiqu.qingjuhe.cn/getip?num=2&type=1&pro=&city=0&yys=0&port=1&pack=19139&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=0&regions="
# # #print (urlopen("http://api.xicidaili.com/free2016.txt").read())
# # #http://icanhazip.com/
# # time.sleep(random.uniform(1, 2))
# # # print (urlopen("http://www.89ip.cn/tqdl.html?api=1&num=30&port=&address=&isp=").read())
# # # date = datetime.datetime.strptime("2018-07-10", "%Y-%m-%d")
# # # print (date.strftime("%Y-%m-%d") < datetime.datetime.today().strftime("%Y-%m-%d"))

# import multiprocessing as mp

# q = mp.Queue()

# q.put({'http': '183.129.207.77:10000'})

# print(type(q.get()))
# print(q.empty())
# print(q.qsize())

# def test():
#     yield 1
#     yield 1
#     yield 0
# for i in test():
#     if i == 1:
#         print (i)
# import datetime
# import tushare as ts
# days = (datetime.datetime.strptime("2018-07-15", "%Y-%m-%d") - datetime.datetime.strptime("2018-07-12", "%Y-%m-%d")).days
# # print(days)
# # for day in range (0, days):
# #     print(day)

# base = datetime.datetime.strptime("2018-07-12", "%Y-%m-%d")
# date_list = [base + datetime.timedelta(days=x) for x in range(0, days + 1)]
# print(date_list)

# df = ts.trade_cal()

# print(df.loc[df["isOpen"] == 1]["calendarDate"].tolist())

# print (ts.trade_cal())

#_*_ coding=utf-8 _*_
# import csv
# from urllib.request import urlopen, Request, HTTPCookieProcessor, build_opener, install_opener, ProxyHandler
# from bs4 import BeautifulSoup
# from urllib.request import HTTPError
# import pandas as pd
# import time
# import http.cookiejar

# csvFile = open("editors.csv",'a+',newline='', encoding='GBK')
# writer = csv.writer(csvFile)
# header = {"Host": "market.finance.sina.com.cn",
#            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
#            "Connection": "keep-alive",
#            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#            "Accept-Ancoding": "gzip, deflate",
#            "Accept-Aanguage": "zh-CN,zh;q=0.9"
#            }
# cj = http.cookiejar.LWPCookieJar()
# cookie_support = HTTPCookieProcessor(cj)
# #proxy_support = ProxyHandler({'http': '138.185.255.74:53281'})
# opener = build_opener(cookie_support)
# install_opener(opener)

# for index in range (1, 2):
#     for _ in range(1):
#         try:
#             print (index)
#             req = Request("http://market.finance.sina.com.cn/transHis.php?symbol=sz002820&date=2016-11-25&page=1", headers = header)
#             #print(req.get_full_url())
#             html = urlopen(req).read().decode('GBK')
#             break
#         except HTTPError as e:
#             print(e)
#     bsObj = BeautifulSoup(html,"html.parser")
#     print (bsObj.findAll("table") == [])
#     table = bsObj.findAll("table")[0] if bsObj.findAll("table") != [] else None
#     if table is None:
#         print("no table");
#         break
#     rows = table.findAll("tr")
#     if len(rows) == 1:
#         break
#     try:
#         for row in rows:
#             csvRow = []
#             for cell in row.findAll(['td','th']):
#                 text = cell.get_text()
#                 if index == 1:
#                     csvRow.append(text.replace(",", ""))
#                 else:
#                     if text not in ["成交时间", "成交价", "价格变动", "成交量(手)", "成交额(元)", "性质"]:
#                         csvRow.append(text.replace(",", ""))
#             if csvRow:
#                 writer.writerow(csvRow)
#     except:
#         pass
#     html = None
#     time.sleep(1)
# csvFile.close()
# df = pd.read_csv("editors.csv", names = ['time', 'price', 'change', 'volume', 'amount', 'type'],
#                    skiprows=[0], encoding = "GBK")

# print (df)

# import datetime
# import time

# start_time = datetime.datetime.now()

# def test():
#     if True:
#         time.sleep(10)
#         global start_time
#         end_time = datetime.datetime.now()
#         print(dir(end_time - start_time))
#         print((end_time - start_time).days)
#         print (datetime.date.today())


# test()

# try:
#     from urllib.request import urlopen, Request
# except ImportError:
#     from urllib2 import urlopen, Request

# def get_tick_data(code=None, date=None, retry_count=3, pause=0.001,
#                   src='sn'):
#     """
#         获取分笔数据
#     Parameters
#     ------
#         code:string
#                   股票代码 e.g. 600848
#         date:string
#                   日期 format: YYYY-MM-DD
#         retry_count : int, 默认 3
#                   如遇网络等问题重复执行的次数
#         pause : int, 默认 0
#                  重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
#         src : 数据源选择，可输入sn(新浪)、tt(腾讯)、nt(网易)，默认sn
#      return
#      -------
#         DataFrame 当日所有股票交易数据(DataFrame)
#               属性:成交时间、成交价格、价格变动，成交手、成交金额(元)，买卖类型
#     """
#     if (src.strip() not in ct.TICK_SRCS):
#         print(ct.TICK_SRC_ERROR)
#         return None
#     symbol = ct._code_to_symbol(code)
#     symbol_dgt = ct._code_to_symbol_dgt(code)
#     datestr = date.replace('-', '')
#     url = {
#             ct.TICK_SRCS[0] : ct.TICK_PRICE_URL % (ct.P_TYPE['http'], ct.DOMAINS['sf'], ct.PAGES['dl'],
#                                 date, symbol),
#             ct.TICK_SRCS[1] : ct.TICK_PRICE_URL_TT % (ct.P_TYPE['http'], ct.DOMAINS['tt'], ct.PAGES['idx'],
#                                            symbol, datestr),
#             ct.TICK_SRCS[2] : ct.TICK_PRICE_URL_NT % (ct.P_TYPE['http'], ct.DOMAINS['163'], date[0:4], 
#                                          datestr, symbol_dgt)
#              }
#     print (url)
#     for _ in range(retry_count):
#         time.sleep(pause)
#         try:
#             if src == ct.TICK_SRCS[2]:
#                 df = pd.read_excel(url[src])
#                 df.columns = ct.TICK_COLUMNS
#             else:
#                 re = Request(url[src])
#                 lines = urlopen(re, timeout=10).read()
#                 lines = lines.decode('GBK') 
#                 if len(lines) < 20:
#                     return None
#                 df = pd.read_table(StringIO(lines), names=ct.TICK_COLUMNS,
#                                    skiprows=[0])      
#         except Exception as e:
#             print(e)
#         else:
#             return df
#     raise IOError(ct.NETWORK_URL_ERROR_MSG)
#     

# import akshare as ak

# stock_zh_a_tick_tx_js_df = ak.stock_zh_a_tick_tx_js(symbol="sz000001")
# print(stock_zh_a_tick_tx_js_df)
# 
# 

#import akshare as ak
# import pandas as pd
# from requests_html import HTMLSession
# import random
# import time
# from typing import Optional
# import asyncio

# def stock_zh_a_hist_requests_html(
#     symbol: str = "000001",
#     period: str = "daily",
#     start_date: str = "19700101",
#     end_date: str = "20500101",
#     adjust: str = "",
#     timeout: float = 30,
#     use_async: bool = False
# ) -> pd.DataFrame:
#     """
#     使用 requests-html 库优化的东方财富网股票历史数据获取
#     支持同步和异步请求，更好的反爬处理能力
#     """
#     # 随机延迟
#     time.sleep(random.uniform(1, 3))
    
#     market_code = 1 if symbol.startswith("6") else 0
#     adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
#     period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
    
#     url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    
#     params = {
#         "fields1": "f1,f2,f3,f4,f5,f6",
#         "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
#         "ut": "7eea3edcaed734bea9cbfc24409ed989",
#         "klt": period_dict[period],
#         "fqt": adjust_dict[adjust],
#         "secid": f"{market_code}.{symbol}",
#         "beg": start_date,
#         "end": end_date,
#         "_": str(int(time.time() * 1000))
#     }
    
#     # 更真实的浏览器头
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
#         "Accept": "application/json, text/plain, */*",
#         "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Connection": "keep-alive",
#         "Referer": f"https://quote.eastmoney.com/concept/{'sh' if market_code == 1 else 'sz'}{symbol}.html",
#         "Sec-Fetch-Dest": "empty",
#         "Sec-Fetch-Mode": "cors",
#         "Sec-Fetch-Site": "same-site",
#         "DNT": "1",
#         "Sec-Ch-Ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
#         "Sec-Ch-Ua-Mobile": "?0",
#         "Sec-Ch-Ua-Platform": '"Windows"'
#     }
    
#     try:
#         # 创建 HTMLSession
#         session = HTMLSession()
#         session.get("https://www.eastmoney.com/")
        
#         if use_async:
#             # 异步请求
#             return asyncio.run(_async_fetch(session, url, params, headers, timeout, symbol))
#         else:
#             # 同步请求
#             return _sync_fetch(session, url, params, headers, timeout, symbol)
            
#     except Exception as e:
#         print(f"请求异常: {e}")
#         return pd.DataFrame()
#     finally:
#         if 'session' in locals():
#             session.close()

# def _sync_fetch(session, url, params, headers, timeout, symbol):
#     """同步请求处理"""
#     response = session.get(
#         url, 
#         params=params, 
#         headers=headers, 
#         timeout=timeout
#     )
    
#     # 使用 requests-html 的渲染能力（如果需要）
#     # response.html.render(sleep=2)  # 如果需要执行JavaScript可以取消注释
    
#     return _process_response(response, symbol)

# async def _async_fetch(session, url, params, headers, timeout, symbol):
#     """异步请求处理"""
#     response = await session.get(
#         url, 
#         params=params, 
#         headers=headers, 
#         timeout=timeout
#     )
    
#     # 异步渲染（如果需要）
#     # await response.html.arender(sleep=2)
    
#     return _process_response(response, symbol)

# def _process_response(response, symbol):
#     """处理响应数据"""
#     if response.status_code != 200:
#         print(f"请求失败，状态码: {response.status_code}")
#         return pd.DataFrame()
    
#     try:
#         data_json = response.json()
#     except Exception as e:
#         print(f"JSON解析失败: {e}")
#         return pd.DataFrame()
    
#     # 检查数据是否有效
#     if not (data_json.get("data") and data_json["data"].get("klines")):
#         print("未获取到有效数据")
#         return pd.DataFrame()
    
#     # 处理数据
#     temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
#     temp_df["股票代码"] = symbol
    
#     # 列名映射
#     column_mapping = {
#         0: "日期", 1: "开盘", 2: "收盘", 3: "最高", 4: "最低", 
#         5: "成交量", 6: "成交额", 7: "振幅", 8: "涨跌幅", 
#         9: "涨跌额", 10: "换手率", 11: "股票代码"
#     }
#     temp_df = temp_df.rename(columns=column_mapping)
    
#     # 数据类型转换
#     numeric_columns = ["开盘", "收盘", "最高", "最低", "成交量", "成交额", 
#                       "振幅", "涨跌幅", "涨跌额", "换手率"]
    
#     temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.date
    
#     for col in numeric_columns:
#         temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
    
#     # 列顺序调整
#     final_columns = [
#         "日期", "股票代码", "开盘", "收盘", "最高", "最低", 
#         "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"
#     ]
    
#     return temp_df[final_columns]

# # 批量获取的异步版本
# async def batch_stock_hist_async(
#     symbols: list,
#     period: str = "daily",
#     start_date: str = "20230101",
#     end_date: str = "20231231",
#     adjust: str = "",
#     delay: float = 1.0
# ) -> dict:
#     """
#     异步批量获取股票历史数据
#     """
#     session = HTMLSession()
#     results = {}
    
#     tasks = []
#     for i, symbol in enumerate(symbols):
#         # 为每个请求添加不同的延迟
#         task_delay = delay + i * 0.5
#         task = _create_async_task(session, symbol, period, start_date, end_date, adjust, task_delay)
#         tasks.append(task)
    
#     # 并发执行所有任务
#     symbol_tasks = list(zip(symbols, tasks))
#     for symbol, task in symbol_tasks:
#         try:
#             df = await task
#             results[symbol] = df
#             print(f"成功获取 {symbol} 的数据，共 {len(df)} 行")
#         except Exception as e:
#             print(f"获取 {symbol} 数据失败: {e}")
#             results[symbol] = pd.DataFrame()
    
#     session.close()
#     return results

# async def _create_async_task(session, symbol, period, start_date, end_date, adjust, delay):
#     """创建异步任务"""
#     await asyncio.sleep(delay)
    
#     market_code = 1 if symbol.startswith("6") else 0
#     adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
#     period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
    
#     url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    
#     params = {
#         "fields1": "f1,f2,f3,f4,f5,f6",
#         "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
#         "ut": "7eea3edcaed734bea9cbfc24409ed989",
#         "klt": period_dict[period],
#         "fqt": adjust_dict[adjust],
#         "secid": f"{market_code}.{symbol}",
#         "beg": start_date,
#         "end": end_date,
#         "_": str(int(time.time() * 1000))
#     }
    
#     headers = {
#         "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(115, 120)}.0.0.0 Safari/537.36",
#         "Accept": "application/json, text/plain, */*",
#         "Referer": f"https://quote.eastmoney.com/concept/{'sh' if market_code == 1 else 'sz'}{symbol}.html",
#     }
    
#     response = await session.get(url, params=params, headers=headers, timeout=30)
#     return _process_response(response, symbol)


# stock_zh_a_hist_df = stock_zh_a_hist_requests_html(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="")
# print(stock_zh_a_hist_df)
# 

import os
import multiprocessing
import requests

def worker_with_env_proxy(url, proxy):
    os.environ['HTTP_PROXY'] = proxy
    os.environ['HTTPS_PROXY'] = proxy
    
    print(f"Process {multiprocessing.current_process().name} set env proxy: {proxy}")
    
    response = requests.get(url)  # 或 third_party_lib.fetch(url)
    return response.text

if __name__ == '__main__':
    proxies = [
        'http://121.43.154.123:8081',
        'http://8.130.36.163:8080',
        'http://8.148.23.202:80',
    ]
    url = 'http://api.ipify.org'
    with multiprocessing.Pool() as pool:
        results = pool.starmap(worker_with_env_proxy, [(url, p) for p in proxies])
    
    for res in results:
        print(res)