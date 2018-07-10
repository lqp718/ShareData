from urllib.request import urlopen, Request

import re
import time
import threading
import socket
import urllib

def get_proxy_list():
    header = {"Host": "www.xicidaili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Ancoding": "gzip, deflate",
            "Accept-Aanguage": "zh-CN,zh;q=0.9"
            }
    ip_l = []
    proxy_l = []
    for page in range (1, 10):
        req = Request("http://www.xicidaili.com/wt/%d" % (page), headers = header)
        lines = urlopen(req, timeout=10).read().decode('utf-8')
        pattern=re.compile(r'<td>(\d.*?)</td>')
        ip_page=re.findall(pattern,str(lines))
        ip_l.extend(ip_page)
        time.sleep(5)

    for i in range(0,len(ip_l),4):
        proxy_host = ip_l[i]+':'+ip_l[i+1]
        proxy_temp = {"http":proxy_host}
        proxy_l.append(proxy_temp)

    return proxy_l

def mp_thread_test(proxys):
    proxy_ip=open('proxy_ip.txt','w')  #新建一个储存有效IP的文档
    lock=threading.Lock()  #建立一个锁
    #验证代理IP有效性的方法
    def test(proxy):
        socket.setdefaulttimeout(5)  #设置全局超时时间
        url = "http://market.finance.sina.com.cn/downxls.php?date=2015-01-05&symbol=sh600050"  #打算爬取的网址
        try:
            proxy_support = urllib.request.ProxyHandler(proxy)
            opener = urllib.request.build_opener(proxy_support)
            opener.addheaders=[("User-Agent","Mozilla/5.0 (Windows NT 10.0; WOW64)")]
            urllib.request.install_opener(opener)
            urllib.request.urlopen(url).read()
            lock.acquire()     #获得锁
            print(proxy,'is OK')        
            proxy_ip.write('%s\n' %str(proxy))  #写入该代理IP
            lock.release()     #释放锁
        except Exception as e:
            lock.acquire()
            print(proxy,e)
            lock.release()
    #单线程验证
    '''for i in range(len(proxys)):
        test(i)'''
    #多线程验证    
    threads=[]
    for ip in proxys:
        thread=threading.Thread(target=test,args=[ip])
        threads.append(thread)
        thread.start()
    #阻塞主进程，等待所有子线程结束
    for thread in threads:
        thread.join()
        
    proxy_ip.close()  #关闭文件

if __name__ == '__main__':
    pl = get_proxy_list()
    mp_thread_test(pl)