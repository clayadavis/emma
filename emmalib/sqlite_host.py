# -*- coding: utf-8 -*-
# emma
#
# Copyright (C) 2006 Florian Schmidt (flo@fastflo.de)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU Library General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301 USA

import pysqlite2.dbapi2 as sqlite3
	
import sys
import time
import re
import traceback
import pprint

from mysql_host import *
from mysql_db import *
from mysql_table import *

class sqlite_table(mysql_table):
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
	
	def __getitem__(self, what):
		print "todo: props dict %r" % what
		return None
		
	def refresh(self, refresh_props=True):
		self.host.query("SELECT sql FROM sqlite_master WHERE type='table' and name='%s'" % self.name)
		result = self.handle.store_result()
		self.fields = {}
		self.field_order = []
		result = result.fetch_row(0)
		self.create_table = result[0][0]

		self.host.query("SELECT * FROM %s limit 1" % self.name)

		for field in self.host.handle.c.description:
			self.field_order.append(field[0])
			self.fields[field[0]] = field

		self.last_field_read = time.time()
		return

	def __str__(self):
		output = ""
		for h, p in zip(self.db.status_headers, self.props):
			output += "\t%-25.25s: %s\n" % (h, p)
		return output
		
	def get_create_table(self):
		if not self.host.query("SELECT sql FROM sqlite_master WHERE type='table' and name='%s'" % self.name): return
		result = self.handle.store_result()
		if not result:
			print "can't get create table for %s at %s and %s" % (self.name, self, self.handle)
			return ""
		result = result.fetch_row(0)
		self.create_table = result[0][0]
		return self.create_table

class sqlite_db(mysql_db):
	def __init__(self, host, name=None):
		self.handle = host.handle
		self.host = host
		self.charset = self.host.charset
		self.name = name
		self.expanded = False
		self.status_headers = []
		self.tables = {}
		
	def __getstate__(self):
		d = dict(self.__dict__)
		for i in ["handle"]:
			del d[i]
		#print "db will pickle:", d
		return d
		
	def refresh(self):
		if not self.host.query("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"): return
		new_tables = []
		result = self.handle.store_result()
		old = dict(zip(self.tables.keys(), range(len(self.tables))))
		for row in result.fetch_row(0):
			if not row[0] in old:
				#print "new table", row[0]
				self.tables[row[0]] = sqlite_table(self, row)
				new_tables.append(row[0])
			else:
				del old[row[0]]
		for table in old:
			del self.tables[table]
		return new_tables

	def query(self, query, check_use=True, append_to_log=True):
		self.host.select_database(self)
		return self.host.query(query, check_use, append_to_log)
	

class sqlite_result(object):
	def __init__(self, result, d):
		self.result = result
		self.description = tuple(d)
	def fetch_row(self, arg):
		return self.result
	def describe(self):
		return self.description
	def num_rows(self):
		return len(self.result)

class sqlite_handle(object):
	def __init__(self, host, connection):
		self.host = host
		self.connection = connection
		self.connection.isolation_level = None
		self.c = self.connection.cursor()
		self.stored_result = False

	def affected_rows(self):
		return 0 # todo

	def insert_id(self):
		return 0 # todo

	def execute(self, query):
		self.c.execute(query)
		self.stored_result = False

	def field_count(self):
		if self.c.description is None:
			return 0
		return len(self.c.description)
			
	def store_result(self):
		self.stored_result = True
		self.result = sqlite_result(self.c.fetchall(), self.c.description)
		return self.result

	def close(self):
		self.connection.close()


class sqlite_host(mysql_host):
	def __init__(self, sql_log, msg_log, filename):
		self.sql_log, self.msg_log, self.filename = sql_log, msg_log, filename
		self.name = self.filename
		self.host = "localhost"
		self.user = os.getenv("USER")
		self.charset = "utf8"
		self.connected = False
		self.expanded = False
		self.handle = None
		self.current_db = None
		self.databases = {}
			
		self.processlist = None
		self.update_ui = None
		self.last_error = ""
		
	def __getstate__(self):
		d = dict(self.__dict__)
		for i in ["sql_log", "msg_log", "handle", "processlist", "update_ui", "update_ui_args"]:
			del d[i]
		#print "host will pickle:", d
		return d
		
	def get_connection_string(self):
		return "::sqlite::"
		
	def set_update_ui(self, update_ui, *args):
		self.update_ui = update_ui
		self.update_ui_args = args
	
	def connect(self):
		try:
			self.handle = sqlite_handle(self, sqlite3.connect(self.filename))
		except:
			self.connected = False
			self.msg_log("%s: %s" % (sys.exc_type, sys.exc_value))
			return
		self.current_db = sqlite_db(self, "dummydb")
		self.databases = {
			"dummydb": self.current_db}
		self.connected = True		
		self.refresh()

	def ping(self):
		return True
		
	def close(self):
		self.databases = {}
		self.processlist = None
		if self.handle:
			self.handle.close()
			self.handle = None
		self.connected = False
		if self.update_ui: self.update_ui(self, *self.update_ui_args)
		
	def query(self, query, check_use=True, append_to_log=True, encoding=None):
		if not self.handle:
			self.msg_log("not connected! can't execute %s, %s, %s" % (query, str(self.handle), str(self)))
			return
		if append_to_log:
			self.sql_log(query)
		try:
			self.query_time = 0
			start = time.time()
			if encoding:
				query = query.encode(encoding, "ignore")
			print "executing query (encoding: %s): %r" % (encoding, query)
			self.handle.execute(query)
			self.query_time = time.time() - start
		except:
			print "error executing query:\n%s" % traceback.format_exc()
			s = str(sys.exc_value)
			self.last_error = s
			self.msg_log(s)
			return False
			
		return True
		
	def _use_db(self, name, do_query=True):
		pass
	def select_database(self, db):
		pass
	def refresh(self):
		pass
	def refresh_processlist(self):
		pass
	def insert_id(self):
		raise Exception("todo") # return self.handle.insert_id()
	def escape(self, s):
		print "todo: sqlite escape!"
		return repr(s)[1:-1]
	def escape_field(self, field):
		print "todo: sqlite escape_field!"
		return field
	def escape_table(self, table):
		return table
		
