from urllib.request import urlopen, Request

import re
import time
import threading
import socket
import urllib
import random
import logging

def get_proxy_list():
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
    for page in range (1, 2):
        #logging.debug("get IP from page %d" % (page))
        #req = Request("http://www.xicidaili.com/wt/%d" % (page), headers = header)
        #req = Request("http://api.xdaili.cn/xdaili-api//greatRecharge/getGreatIp?spiderId=03d973cf76f94aca9887e84868453d59&orderno=YZ20187222643m2Bwb7&returnType=1&count=15", headers = header)
        req = Request("http://dec.ip3366.net/api/?key=20180722175459925&getnum=15&isp=1&anonymoustype=1&filter=1&area=1&proxytype=0", headers = header)
        try:
            lines = urlopen(req, timeout=10).read().decode('utf-8')
            # pattern=re.compile(r'<td>(\d.*?\d)</td>')
            # ip_page=re.findall(pattern,str("".join(lines.split())))
            # ip_l.extend(ip_page)
            # print(lines.split("\r\n"))
            ip_l = lines.split("\r\n")
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
        socket.setdefaulttimeout(5)
        urls = ["http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?", "http://market.finance.sina.com.cn/transHis.php?"]
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
        except Exception as e:
            pass

    threads=[]
    for ip in proxys:
        thread=threading.Thread(target=test,args=[ip])
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    logging.debug("Proxy list passed the test \n%s" % (proxy_ip))
    return proxy_ip

def get_proxy():
    while True:
        pl = get_proxy_list()
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
    get_proxy()
    #get_proxy_list()