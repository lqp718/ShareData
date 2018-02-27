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
		return self.Collection.find(filter = _filter, projection = _projection, sort = _sort)

	def update(self, _filter, _update):
		return self.Collection.update_one(filter = _filter, update = _update)

	def logout(self):
		self.db.logout()

# Test code>>>
if __name__ == '__main__':
	database = DB("MyShare", "600050")
	print database.Collection.count()
	for item in database.find(_filter = {'date' : {"$lte": "2015-01-07", "$gte": "2015-01-06"}}):
		print item["date"]
# Test code<<<
