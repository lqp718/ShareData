import tushare as ts
import time
from pandas import DataFrame as DF
import config as cfg

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
		if self.ShareDf.empty:
			self.ShareDf = self.ShareDf.append(df, ignore_index = True)
		else:
			if not self.ShareDf.tail(1).equals(df):
				self.ShareDf = self.ShareDf.append(df, ignore_index = True)
		time.sleep(1)

if __name__ == '__main__':
	RT = Realtime()
	while True:
		RT.get()
