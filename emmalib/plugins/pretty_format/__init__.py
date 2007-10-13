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

import os
import sys
import time
import gtk.glade
import gobject
import pprint
import re
import cStringIO

def test(c, t, f):
	if c:
		return t
	return f

def strspn(text, accept, pos=0):
	tl = len(text)
	start = pos
	while pos < tl and text[pos] in accept:
		pos += 1
	return pos - start

def strcspn(text, reject, pos=0):
	tl = len(text)
	start = pos
	while pos < tl and text[pos] not in reject:
		pos += 1
	return pos - start


def search_string_end(text, delim, p):
	s = p
	while True:
		l = strcspn(text, delim, s)
		# check if there is an odd count of backslashes before
		r = s + l - 1
		count = 0
		while text[r] == "\\":
			r -= 1
			count += 1
		escaped = count % 2 == 1
		if not escaped:
			break
		s = s + l
	return s + l

def search_parenthesis_end(text, s):
	# search closing ) jumping over quoted strings
	opens = 1
	s += 1
	while True:
		#print "search closing: %r" % text[s:]
		el = strcspn(text, "()\"'", s)
		end = s + el
		print "ptoken: %r" % text[end]
		if text[end] == "(":
			opens += 1
			#print "now open:", opens
			s = end + 1
			continue
		if text[end] == ")":
			opens -= 1
			#print "now open:", opens
			s = end + 1
			if opens == 0:
				break
			continue
		# must be a string
		delim = text[end]
		strend = search_string_end(text, delim, end + 1)
		quoted_string = text[end:strend + 1]
		#print "quoted string: %r" % quoted_string
		s = strend + 1
	return s

def get_token(text, p, allow_functions=False):
	ttype = "token"
	o = strspn(text, " \r\n\t", p)
	p = p + o
	print "\nget token from %r" % text[p:p + 25]
	if not text[p:]:
		return ttype, "", len(text)

	if text[p] in "\"'":
		delim = text[p]
		end = search_string_end(text, delim, p + 1)
		quoted_string = text[p:end + 1]
		#print "quoted string: %r" % quoted_string
		ttype = "quoted string"
		return ttype, quoted_string, end + 1

	l = strcspn(text, " \r\n\t(,;=", p)
	s = p + l
	if s >= len(text):
		print "********last token? : %r" % text[p:] # todo?
		return ttype, text[p:], len(text)

	print "found first    %r" % text[s]
	if text[s] == "(":
		s = search_parenthesis_end(text, s)
		if l == 0:
			ttype = "parenthesis block"
		else:
			ttype = "function call"
		l = s - p
	elif text[s] in "=,;" and l == 0:
		l = 1
	else:
		pp = p + l
		wl = strspn(text, " \r\n\t", pp)
		pp += wl
		print "first char after: %r" % text[pp]
		if text[pp] == "(":
			# found function call
			# read function arguments to this token
			s = search_parenthesis_end(text, pp)
			l = s - p
			ttype = "function call"
		
	token = text[p:p + l]
	return ttype, token, p + l

def pretty_print_function_call(function, compressed=False):
	l = strcspn(function, "(\n\r\t ")
	function_name = function[:l]
	ll = strspn(function, "\n\r\t ", l)
	function_args = function[l + ll + 1:-1]
	print "function name: %r args: %r" % (function_name, function_args)
	out = function_name + "("
	p = 0
	tl = len(function_args)
	while p < tl:
		tt, token, e = get_token(function_args, p)
		if not token:
			break
		print "fcn pf: token: %r type: %s" % (token, tt)
		if tt == "function call":
			# uniform pretty print a function call
			token = pretty_print_function_call(token)
		if not compressed and token == ",":
			out += token + " "
		else:
			out += token
		p = e
	return out + ")"


class pretty_format:
	def __init__(self, emma_instance):
		self.emma = emma_instance
		self.toolbar_items = []
		self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

		self.install_toolbar_item("query_toolbar", gtk.STOCK_INDENT, "pretty format query", self.on_pretty_format)
		self.install_toolbar_item("query_toolbar", gtk.STOCK_UNINDENT, "compress query", self.on_compress)
		q = self.emma.current_query
		if sys.stdout.debug and 0:
			# check if we are running with debug output - enable example text
			print "\n\n\n"
			self.set_query_text(q, """# this is the pretty format test query. click the "pretty format" or "compress query" button in the query-toolbar.
       \n      \t# comment before\n\n/* also before... */\n   \tselect date_format \n\t (\nnow(  \n"lalala"  ) , "%Y-%m-%d"  \n), ("%Y,((%m"), \', from ),here\', * from record_job 
where some_field
= 
"a very interesting 'text'"
order by job_id desc,
\tvalid_from,\n\t\t\n\tmode,\n\tquery,\n\tpriority desc limit 150;
select * from user;
""")


	def cleanup(self):
		for item, toolbar in self.toolbar_items:
			toolbar.remove(item)		
			del item
		
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

	def on_pretty_format(self, button):
		q = self.emma.current_query
		text = self.get_query_text(q)
		print "input: %r" % text
		try:
			sql = reload(self.emma.sql)
		except:
			print traceback.format_exc()
			return
		try:
			r = sql.grammer.parseString(text)
			#r = sql.field_list.parseString(text)
		except:
			print sys.exc_type, sys.exc_value
			print sys.exc_value.__dict__
			return

		output = cStringIO.StringIO()
		def do(token, depth=0, do_newline=True):
			for t in token:
				if type(t) == str:
					if do_newline and t not in ("(", ")"):
						output.write("\t" * depth)
					elif do_newline and t in ("(", ")"):
						output.write("\t" * (depth - 1))
					elif t not in (",", "left join"):
						output.write(" ")
					elif t in ("left join"):
						output.write("\n" + "\t" * (depth - 1))
					output.write(t)
					if t in (",", "(", "select", "from", "left join", "where"):
						output.write("\n")
						do_newline = True
					else:
						do_newline = False
				else:
					do_newline = do(t, depth + 1, do_newline)
			output.write("\n")
			return True
		pprint.pprint(r)
		do(r)
		print output.getvalue()
		
		#self.set_query_text(q, output.getvalue())

	def on_compress(self, button):
		q = self.emma.current_query
		text = self.get_query_text(q)
		print "input: %r" % text
		
		#keywords = "select,from,left,join,right,inner,where,and,or,on,order,by,having,group,limit,union,distinct"
		#if tt == "function call":
		try:
			r = self.emma.sql.grammer.parseString(code)
		except:
			print sys.exc_type, sys.exc_value
			return

		output = []
		#self.set_query_text(q, output.getvalue())

		
plugin_instance = None	
def plugin_init(emma_instance):
	global plugin_instance
	plugin_instance = pretty_format(emma_instance)
	return plugin_instance
	
def plugin_unload():
	global plugin_instance
	plugin_instance.cleanup()
	del plugin_instance
	plugin_instance = None
	gc.collect()
