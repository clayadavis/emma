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
		
	def refresh(self, refresh_props = True):
		self.db.host.select_database(self.db)
		
		if refresh_props:
			self.host.query("show table status like '%s'" % self.name)
			result = self.handle.store_result()
			self.props = result.fetch_row(0)
			self.name = self.props[0][0]
		
		self.host.query("describe `%s`" % self.name)
		result = self.handle.store_result()
		self.fields = {}
		self.field_order = []
		for row in result.fetch_row(0):
			self.field_order.append(row[0])
			self.fields[row[0]] = row
		self.last_field_read = time.time()
		return
