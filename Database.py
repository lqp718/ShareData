from pymongo import MongoClient

class DB():
	def __init__(self, db, col, host=None, port=None,):
		self.conn = MongoClient(host = host, port = port)
		self.db = self.conn[db]
		self.Collection = self.db.get_collection(name = col)
		if self.Collection is None:
			self.Collection = self.db.create_collection(name = col)

	def insert_one(self, _dic):
		return self.Collection.insert_one(_dic)

	def find(self, _filter, _projection = {'_id': False}, _sort = None):
		i = 0
		result = []
		for item in self.Collection.find(filter = _filter, projection = _projection, sort = _sort):
			result.append(item)
			i += 1
		return i, result

	def update(self, _filter, _update, _upsert = False):
		return self.Collection.update_one(filter = _filter, update = _update, upsert = _upsert)

	def logout(self):
		self.db.logout()

# Test code>>>
if __name__ == '__main__':
	database = DB("MyShare", "601901")
	import datetime
	date = datetime.datetime.strptime("2016-01-18", "%Y-%m-%d")
	print database.find(_filter = {'date' : {"$lt": date}})
# Test code<<<
