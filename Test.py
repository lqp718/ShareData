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
import csv
from urllib.request import urlopen, Request, HTTPCookieProcessor, build_opener, install_opener, ProxyHandler
from bs4 import BeautifulSoup
from urllib.request import HTTPError
import pandas as pd
import time
import http.cookiejar

csvFile = open("editors.csv",'a+',newline='', encoding='GBK')
writer = csv.writer(csvFile)
header = {"Host": "market.finance.sina.com.cn",
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
           "Connection": "keep-alive",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
           "Accept-Ancoding": "gzip, deflate",
           "Accept-Aanguage": "zh-CN,zh;q=0.9"
           }
cj = http.cookiejar.LWPCookieJar()
cookie_support = HTTPCookieProcessor(cj)
#proxy_support = ProxyHandler({'http': '138.185.255.74:53281'})
opener = build_opener(cookie_support)
install_opener(opener)

for index in range (1, 2):
    for _ in range(1):
        try:
            print (index)
            req = Request("http://market.finance.sina.com.cn/transHis.php?symbol=sz002820&date=2016-11-25&page=1", headers = header)
            #print(req.get_full_url())
            html = urlopen(req).read().decode('GBK')
            break
        except HTTPError as e:
            print(e)
    bsObj = BeautifulSoup(html,"html.parser")
    print (bsObj.findAll("table") == [])
    table = bsObj.findAll("table")[0] if bsObj.findAll("table") != [] else None
    if table is None:
        print("no table");
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
    html = None
    time.sleep(1)
csvFile.close()
df = pd.read_csv("editors.csv", names = ['time', 'price', 'change', 'volume', 'amount', 'type'],
                   skiprows=[0], encoding = "GBK")

print (df)

