import tushare as ts
import time
from pandas import DataFrame as df
import config as cfg
import json

per_price = None
per_volume = None
per_amount = None

class Realtime():
	def __init__(self):
		self.ShareDetail = df()
		self.ShareInfo = df()
		self.high = 0
		self.low = 0
		pass

	def __del__(self):
		pass

	def get(self):
		df = ts.get_realtime_quotes(cfg.ShareCode)

		if df is not None:

			if self.ShareInfo.empty:
				self.ShareInfo = df.loc[:, ['date', 'open', 'pre_close']]

			if self.high == 0 or self.high <= df['high'].values[0]:
				self.high = df['high'].values[0]

			if self.low == 0 or self >= df['low'].values[0]:
				self.low = df['low'].values[0]

			vls = [cls for cls in df.columns if '_v' in cls]
			pls = [cls for cls in df.columns if '_p' in cls]

			df = df.loc[:,['time'] + ['price'] + vls + pls]

			if self.ShareDetail.empty:
				self.ShareDetail = self.ShareDetail.append(df, ignore_index = True)
			else:
				tail = self.ShareDetail.tail(1).reset_index(drop = True)
				if not tail.equals(df):
					self.ShareDetail = self.ShareDetail.append(df, ignore_index = True)

#Test code>>>
if __name__ == '__main__':
	RT = Realtime()
	while True:
		RT.get()
		time.sleep(1)
		print RT.ShareDetail
#Test code<<<
