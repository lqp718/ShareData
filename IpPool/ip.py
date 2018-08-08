from urllib.request import urlopen, Request

import re
import time
import threading
import socket
import urllib
import random
import logging
import datetime

start_time = datetime.datetime.now()

total_ip = 0

def get_proxy_list(count = 1, retry = 3):
    global start_time
    global total_ip
    if count > 10:
        count = 10

    total_ip = total_ip + count
    header = {#"Host": "www.xicidaili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Ancoding": "gzip, deflate",
            "Accept-Aanguage": "zh-CN,zh;q=0.9"
            }
    ip_l = []
    proxy_l = []
    opener = urllib.request.build_opener()
    urllib.request.install_opener(opener)
    #for page in random.sample(range (1, 6), 5):
    for _ in range (retry):
        #logging.debug("get IP from page %d" % (page))
        #req = Request("http://www.xicidaili.com/wt/%d" % (page), headers = header)
        try:
            req = Request("http://http.tiqu.qingjuhe.cn/getip?num=%d&type=1&pro=&city=0&yys=0&port=1&pack=19610&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=0&regions=" % (count), headers = header)
            lines = urlopen(req, timeout=10).read().decode('utf-8')
            if "您的套餐今日已到达上限" in lines:
                logging.debug("今日已到达上限")
                end_time = datetime.datetime.now()
                logging.debug("共用时 %ds 共获取 %d IP" % ((end_time - start_time).seconds, total_ip))
                today = datetime.date.today()
                while True:
                    tomorrow = datetime.date.today()
                    if (tomorrow - today).days == 1:
                        logging.debug("New days begin!!!")
                        start_time = datetime.datetime.now()
                        break
                    time.sleep(3600)
                break
            # pattern=re.compile(r'<td>(\d.*?\d)</td>')
            # ip_page=re.findall(pattern,str("".join(lines.split())))
            # ip_l.extend(ip_page)
            ip_l = lines.split("\r\n")
            break
        except:
            pass
        time.sleep(5)

    # for i in range(0,len(ip_l),3):
    #     proxy_host = ip_l[i]+':'+ip_l[i+1]
    #     proxy_temp = {"http":proxy_host}
    #     proxy_l.append(proxy_temp)
    for proxy_host in ip_l:
        if proxy_host != "":
            proxy_temp = {"http":proxy_host}
            proxy_l.append(proxy_temp)

    logging.debug("collected IP count \n%d" % (len(proxy_l)))
    return proxy_l

def mp_thread_test(proxys):
    proxy_ip=[]
    lock=threading.Lock()

    def test(proxy):
        socket.setdefaulttimeout(10)
        urls = ["http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?", "http://market.finance.sina.com.cn/transHis.php?"]
        for _ in range(3):
            try:
                proxy_support = urllib.request.ProxyHandler(proxy)
                opener = urllib.request.build_opener(proxy_support)
                opener.addheaders=[("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",)]
                urllib.request.install_opener(opener)
                for url in urls:
                    lines = urlopen(url).read().decode('GBK')

                if lines == "Param date cannot be empty!":
                    lock.acquire()
                    # print(proxy, lines)
                    proxy_ip.append(proxy)
                    lock.release()
                    break
            except Exception as e:
                pass
            time.sleep(4)

    threads=[]
    for ip in proxys:
        thread=threading.Thread(target=test,args=[ip])
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    logging.debug("%d proxy passed the test \n%s" % (len(proxy_ip), proxy_ip))
    return proxy_ip

def get_proxy(count = 1):
    while True:
        pl = get_proxy_list(count)
        proxy_list = mp_thread_test(pl)
        if proxy_list:
            break
        time.sleep(10)
    return proxy_list

if __name__ == '__main__':
    log_file = "proxy_test.log"
    console_logger = logging.FileHandler(filename = log_file, mode = 'a', encoding="utf-8", delay=True)
    logging.getLogger().setLevel(logging.DEBUG)
    console_logger.setLevel(logging.NOTSET)
    console_logger.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(console_logger)
    get_proxy(count = 1)
    #get_proxy_list()