# -*- coding: utf-8 -*-
import config as cfg
import tushare as ts

df = ts.get_tick_data(cfg.ShareCode, date='2017-08-31', src='tt')
print df.head(len(df)).replace("买盘", "Buy").replace("卖盘", "Sel").replace("中性盘", "Non")