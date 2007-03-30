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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

# code from here is shamelessly stolen from pysnippet:
#  http://sourceforge.net/projects/pysnippet/

import os
import sys
import time
import gtk.glade
import gobject
import pprint
import re
import cStringIO
import string
import StringIO

import snippet.tokenize as tokenize

class syntax_highlight:
	def __init__(self, emma_instance):
		self.emma = emma_instance
		self.toolbar_items = []
		self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

		self.load_config()

		self.install_toolbar_item("query_toolbar", gtk.STOCK_INDENT, "do SH", self.do_sh)
		q = self.emma.current_query
		if sys.stdout.debug:
			# check if we are running with debug output - enable example text
			self.set_query_text(q, """select * from user;""")
			self.do_sh(None)

	def cleanup(self):
		for item, toolbar in self.toolbar_items:
			toolbar.remove(item)		
			del item

	def load_config(self):
		self.keywords = "select,from,where,limit,left,right,inner,outer,join,order,by"
		self.keywords = set(self.keywords.split(","))
		
	def install_toolbar_item(self, toolbar_name, stock, item_catpion, callback):
		toolbar = self.emma.xml.get_widget(toolbar_name)
		button = gtk.ToolButton(stock)
		button.set_label(item_catpion)
		button.connect("clicked", callback)
		button.set_tooltip(self.emma.tooltips, item_catpion)
		toolbar.insert(button, -1)
		button.show()
		self.toolbar_items.append((button, toolbar)) 

	def get_query_text(self, q):
		buffer = q.textview.get_buffer()
		return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())

	def set_query_text(self, q, text):
		buffer = q.textview.get_buffer()
		buffer.set_text(text)

	def do_sh(self, button):
		buffer = self.emma.current_query.textview.get_buffer()
		self.populate_buffer(buffer)
		start, end = buffer.get_bounds()
		buffer.remove_all_tags(start, end)

		code = buffer.get_text(start, end)
		for tag, (srow, scol), (erow, ecol) in self.scan(code):
		  start = buffer.get_iter_at_line_offset (srow-1, scol)
		  end   = buffer.get_iter_at_line_offset (erow-1, ecol)
		  buffer.apply_tag_by_name (tag, start, end)

	def populate_buffer (self, buffer):
		tags = (
			("keyword", "#0000ff"),
			("string",  "#004488"),
			("comment", "#009900"),
			("constant","#e07818"))
		for name, color in tags:
			try:
				buffer.create_tag("sql_%s" % name,  foreground=color)
			except:
				pass

	def scan (self, code):
		fp = StringIO.StringIO (code)
		state = 0
		chars = string.uppercase + '_'

		try:
			for type, text, (srow, scol), (erow, ecol), line in tokenize.generate_tokens(fp.readline):
				tag = None
				print text
				if type == tokenize.NAME and text in self.keywords:
					tag = "sql_keyword"

				elif type == tokenize.STRING:
					tag = "sql_string"

				elif type == tokenize.COMMENT:
					tag = "sql_comment"

				if state == 0:
					if text == 'gtk':
						state = 1
						c_srow = srow
						c_scol = scol
						
					elif text == 'gobject':
						state = 3
						c_srow = srow
						c_scol = scol

				elif state == 1:
					if text == '.':
						state = 2
					else:
						state = 0

				elif state == 2:
					if text == 'gdk':
						state = 3
					elif False not in [c in chars for c in text]:
						tag = 'sql_constant'
						srow = c_srow
						scol = c_scol
						state = 0
					else:
						state = 0

				elif state == 3:
					if text == '.':
						state = 4
					else:
						state = 0

				elif state == 4:
					if False not in [c in chars for c in text]:
						tag = 'sql_constant'
						srow = c_srow
						scol = c_scol
						state = 0
						
				if tag:
					yield tag, (srow, scol), (erow, ecol)
		except tokenize.TokenError, e:
			pass



		
plugin_instance = None	
def plugin_init(emma_instance):
	global plugin_instance
	plugin_instance = syntax_highlight(emma_instance)
	return plugin_instance
	
def plugin_unload():
	global plugin_instance
	plugin_instance.cleanup()
	del plugin_instance
	plugin_instance = None
	gc.collect()
