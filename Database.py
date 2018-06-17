from pymongo import MongoClient
import pymongo
#from bson.json_util import dumps, loads
import bson
from pandas import DataFrame as DF
import json
from bson import json_util
import pprint


class DB():
	def __init__(self, db, col, host=None, port=None,):
		self.conn = MongoClient(host = host, port = port)
		self.db = self.conn[db]
		self.Collection = self.db.get_collection(name = col)
		if self.Collection is None:
			self.Collection = self.db.create_collection(name = col)

	def insert_one(self, _dic):
		return self.Collection.insert_one(_dic)

	def find(self, _filter = None, _projection = {'_id': False}, _sort = None):
		result = []
		cursor = self.Collection.find(filter = _filter, projection = _projection, sort = _sort)
		# print 
		# for item in cursor:
		# 	print type(item)
		# 	result.append(item)
		# 	i += 1
		result = list(cursor)
		return len(result), result

	def update(self, _filter, _update, _upsert = False):
		return self.Collection.update_one(filter = _filter, update = _update, upsert = _upsert)

	def logout(self):
		self.db.logout()

	def ConstructionDf(self, input_data = None):
		date_index = []
		data = []

		for l in input_data:
			date_index.append(l["date"])
			data.append(l["k_data"])

		k_columns = ["open", "close", "high", "low", "price_change", "p_change", "turnover", "ma5", "ma10", "ma20", "v_ma5", "v_ma10", "v_ma20", "volume"]
		return DF(data = data, index = date_index, columns = k_columns)

# Test code>>>
if __name__ == '__main__':
	database = DB("MyShare", "600050")
	import datetime
	date = datetime.datetime.strptime("2016-01-15", "%Y-%m-%d")
	i, result = database.find(_filter = {'date' : {"$lt": date}}, _projection = {'_id': False, 'tick': False})
	print (database.ConstructionDf(result))
# Test code<<<