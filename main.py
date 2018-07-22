import multiprocessing as mp
import logging, logging.config, logging.handlers
import time
import random
import urllib
import http.cookiejar

from ShareDB import ShareDB
from Database import DB
from IpPool.ip import get_proxy
from urllib.request import HTTPCookieProcessor, build_opener, install_opener, ProxyHandler

def get_stock_list():
    db = DB("MyShare", "Stockinfo")
    i, result = db.find(_filter = {})
    sList = []
    for index in range(0, i):
        sList.append(result[index]["code"])
    return sList

def split_stock_list(s_list = None, split = 10):
    list_len = len(s_list)
    len_pre_item = list_len // split
    splited_list = []
    index = 0
    while index < list_len:
        splited_list.append(s_list[index : index + len_pre_item])
        index = index + len_pre_item
    return splited_list

def stockdb_task(stocklist = [], process_id = 0, proxy_queue = None):
    log_file = "./log/ShareDB.log"
    console_logger = logging.FileHandler(filename = log_file, mode = 'a', encoding="utf-8", delay=True)
    logging.getLogger().setLevel(logging.DEBUG)
    console_logger.setLevel(logging.NOTSET)
    console_logger.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(console_logger)
    logging.getLogger().handlers[0].baseFilename = "./log/ShareDB_%s.log" % (process_id)
    Share = ShareDB()

    cj = http.cookiejar.LWPCookieJar()
    cookie_support = HTTPCookieProcessor(cj)
    proxy = proxy_queue.get()
    proxy_support = ProxyHandler(proxy)
    opener = build_opener(cookie_support, proxy_support)
    install_opener(opener)
    for code in stocklist:
        for tmp in Share.GetHistoryData(sharecode = code, startdate = "2018-07-03"):
            proxy = proxy_queue.get()
            logging.error("update proxy %s" % (proxy))
            cj = http.cookiejar.LWPCookieJar()
            cookie_support = HTTPCookieProcessor(cj)
            proxy = proxy_queue.get()
            proxy_support = ProxyHandler(proxy)
            opener = build_opener(cookie_support, proxy_support)
            install_opener(opener)
        #logging.getLogger().handlers[0].close()

def update_proxy(q, e):
    log_file = "./log/proxy.log"
    console_logger = logging.FileHandler(filename = log_file, mode = 'a', encoding="utf-8", delay=True)
    logging.getLogger().setLevel(logging.DEBUG)
    console_logger.setLevel(logging.NOTSET)
    console_logger.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(console_logger)

    logging.debug("Collecting Proxy...")
    proxy_list = get_proxy()
    for p in proxy_list:
        q.put(p)

    while e.is_set():
        if q.empty():
            logging.debug("proxy queue is empty, re-collect proxy")
            proxy_list = get_proxy()
            for p in proxy_list:
                q.put(p)
        time.sleep(10)

if __name__ == '__main__':
    stock_list = get_stock_list()
    splited_list = split_stock_list(s_list = stock_list, split = 10)

    q = mp.Queue()

    #Create process to update the proxy queue
    do_update_proxy = mp.Event()
    do_update_proxy.set()
    proxy_process = mp.Process(target=update_proxy, args=(q, do_update_proxy,))
    proxy_process.start()

    #Create process to collect the stock data
    process_id = 0
    procs = list()
    for li in splited_list:
        proc = mp.Process(target=stockdb_task, args=(li, process_id, q,))
        process_id = process_id + 1
        procs.append(proc)
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    do_update_proxy.clear()



    