import multiprocessing as mp
from ShareDB import ShareDB
from Database import DB
import logging, logging.config, logging.handlers

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

def stockdb_task(stocklist = []):
    log_file = "./log/ShareDB.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(message)s",
        )
    console_logger = logging.FileHandler(filename = log_file, encoding="utf-8", delay=True)
    console_logger.setLevel(logging.DEBUG)
    console_logger.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(console_logger)
    Share = ShareDB()
    for code in stocklist:
        logging.getLogger().handlers[0].baseFilename = "./log/ShareDB_%s.log" % (code)
        Share.GetHistoryData(sharecode = code, startdate = "2018-07-03")
    
    logging.shutdown()



if __name__ == '__main__':
    stock_list = get_stock_list()
    splited_list = split_stock_list(s_list = stock_list, split = 10)
    print (splited_list)
    procs = list()
    for li in splited_list:
        proc = mp.Process(target=stockdb_task, args=(li,))
        procs.append(proc)
    for p in procs:
        p.start()
    for p in procs:
        p.join()



    