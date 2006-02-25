import sys
import _mysql
import _mysql_exceptions
import time
import re
from mysql_db import *

class mysql_host:
	def __init__(self, *args):
		self.sql_log, self.msg_log, self.name, self.host, self.port, self.user, self.password, self.database = args
		self.connected = False
		self.databases = {} # name -> db_object
		self.current_db = None
		self.handle = None
		self.processlist = None
		self.update_ui = None
		self.expanded = False
		
	def set_update_ui(self, update_ui, *args):
		self.update_ui = update_ui
		self.update_ui_args = args
	
	def connect(self):
		try:
			self.handle = _mysql.connect(self.host, self.user, self.password, connect_timeout=7)
		except _mysql_exceptions.OperationalError:
			self.connected = False
			self.msg_log("%s: %s" % (sys.exc_type, sys.exc_value[1]))
			return
		self.connected = True
		if self.database: self._use_db(self.database)
		
	def close(self):
		self.databases = {}
		self.processlist = None
		self.handle = None
		self.current_db = None
		self.connected = False
		if self.update_ui: self.update_ui(self, *self.update_ui_args)
		
	def query(self, query, check_use=True):
		if not self.handle:
			self.msg_log("not connected! can't execute %s" % query)
			return
			
		self.sql_log(query)
		try:
			self.query_time = 0
			start = time.time()
			self.handle.query(query)
			self.query_time = time.time() - start
		except:
			print "error code:", sys.exc_value[0]
			self.last_error = sys.exc_value[1]
			self.msg_log(sys.exc_value[1])
			if sys.exc_value[0] == 2013:
				# lost connection
				self.close()
			return False
			
		if not check_use: return True
		match = re.match("(?is)^([ \r\n\t]*|#[^\n]*)*(use[ \r\n\t]*).*", query)
		if match:
			dbname = query[match.end(2):].strip("`; \t\r\n")
			print "use db: '%s'" % dbname
			self._use_db(dbname, False)
			# reexecute to reset field_count and so on...
			self.handle.query(query)
		return True
		
	def _use_db(self, name, do_query=True):
		if self.current_db and name == self.current_db.name: return
		if do_query: self.query("use `%s`" % name, False)
		try:
			self.current_db = self.databases[name]
		except KeyError:
			print "Warning: used an unknown database %s! please refresh host!" % name
		
	def select_database(self, db):
		self._use_db(db.name)
		
	def refresh(self):
		self.query("show databases")
		result = self.handle.store_result()
		old = set(self.databases.keys())
		db_id = len(old)
		for row in result.fetch_row(0):
			if not row[0] in old:
				self.databases[row[0]] = mysql_db(self, row[0])
			else:
				del old[row[0]]
		for db in old:
			print "remove database", db
			del self.databases[db]
		
	def refresh_processlist(self):
		if not self.query("show processlist"): return
		result = self.handle.store_result()
		self.processlist = (result.describe(), result.fetch_row(0))
		
	def escape(self, s):
		return self.handle.escape_string(s)
	