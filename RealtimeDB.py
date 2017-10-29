import tushare as ts
import time
from pandas import DataFrame as DF
import config as cfg
import json

per_price = None
per_volume = None
per_amount = None

class Realtime():
	def __init__(self):
		self.ShareDf = DF()
		pass

	def __del__(self):
		pass

	def get(self):
		df = ts.get_realtime_quotes(cfg.ShareCode)
		if df is not None:
			if self.ShareDf.empty:
				self.ShareDf = self.ShareDf.append(df, ignore_index = True)
			else:
				tail = self.ShareDf.tail(1).reset_index(drop = True)
				if not tail.equals(df):
					self.ShareDf = self.ShareDf.append(df, ignore_index = True)

#Test code>>>
if __name__ == '__main__':
	RT = Realtime()
	while True:
		RT.get()
		time.sleep(1)
		print RT.ShareDf
#Test code<<<
