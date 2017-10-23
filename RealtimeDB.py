import tushare as ts
import time
from pandas import DataFrame as DF

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
		while True:
			df = ts.get_realtime_quotes("600050")

			if self.ShareDf.empty:
				self.ShareDf = self.ShareDf.append(df, ignore_index = True)
			else:
				# print str(getattr(df["time"], "values")[0])
				# print str(getattr(ShareDf.iloc[-1:]["time"], "values")[0])
				if str(getattr(df["time"], "values")[0]) != str(getattr(self.ShareDf.iloc[-1:]["time"], "values")[0]):
					self.ShareDf = self.ShareDf.append(df, ignore_index = True)
			time.sleep(1)

