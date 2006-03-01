import sys, time

class mysql_table:
	def __init__(self, db, props):
		self.handle = db.handle
		self.host = db.host
		self.db = db
		self.props = props
		self.name = props[0]
		self.fields = {}
		self.field_order = []
		self.expanded = False
		self.last_field_read = 0
		self.create_table = ""
		self.describe_headers = []
		
	def __getstate__(self):
		d = dict(self.__dict__)
		for i in ["handle"]:
			del d[i]
		#print "table will pickle:", d
		return d
		
	def refresh(self, refresh_props = True):
		self.db.host.select_database(self.db)
		
		if refresh_props:
			self.host.query("show table status like '%s'" % self.name)
			result = self.handle.store_result()
			rows = result.fetch_row(0)
			self.props = rows[0]
			self.name = self.props[0]
		
		self.host.query("describe `%s`" % self.name)
		result = self.handle.store_result()
		self.describe_headers = []
		for h in result.describe():
			self.describe_headers.append(h[0])
		self.fields = {}
		self.field_order = []
		for row in result.fetch_row(0):
			self.field_order.append(row[0])
			self.fields[row[0]] = row
		self.last_field_read = time.time()
		return

	def __str__(self):
		output = ""
		for h, p in zip(self.db.status_headers, self.props):
			output += "\t%-25.25s: %s\n" % (h, p)
		return output
		
	def get_create_table(self):
		if not self.create_table:
			self.db.host.select_database(self.db)
			self.host.query("show create table `%s`" % self.name)
			print "create with:", self.handle
			result = self.handle.store_result()
			if not result:
				print "can't get create table for %s at %s and %s" % (self.name, self, self.handle)
				return ""
			result = result.fetch_row(0)
			self.create_table = result[0][1]
		return self.create_table
