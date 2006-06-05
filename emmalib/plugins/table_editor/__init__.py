import os
import sys
import time
import gtk.glade
import gobject
import pprint
import re
pp = pprint.PrettyPrinter()

LEN = 1
UNSIGNED = 2
BINARY = 4
ZERO = 8

data_type_capabilities = {
	"bigint": LEN | UNSIGNED | ZERO,
	"blob": LEN,
	"char": LEN | BINARY,
	"char unicode": LEN,
	"date": 0,
	"datetime": 0,
	"decimal": LEN | UNSIGNED | ZERO,
	"double": LEN | UNSIGNED | ZERO,
	"enum": LEN,
	"float": LEN | UNSIGNED | ZERO,
	"int": LEN | UNSIGNED | ZERO,
	"longblob": 0,
	"longtext": 0,
	"mediumblob": 0,
	"mediumint": LEN | UNSIGNED | ZERO,
	"mediumtext": 0,
	"set": LEN,
	"smallint": LEN | UNSIGNED | ZERO,
	"text": LEN,
	"time": 0,
	"year": LEN,
	"timestamp": LEN,
	"tinyblob": 0,
	"tinyint": LEN | UNSIGNED | ZERO,
	"tinytext": LEN | UNSIGNED | ZERO,
	"varchar": LEN | BINARY
}

def split_strings(string):
	return re.findall("(?:(?:'.*?')|[^ ])+", string)

def test(c, t, f):
	if c:
		return t
	return f

class table_editor:
	def __init__(self, emma_instance):
		self.emma = emma_instance
		self.popup_items = []
		
		self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
		self.glade_file = os.path.join(self.plugin_dir, "table_editor.glade")
		if not os.access(self.glade_file, os.R_OK):
			raise ValueError("galde file %s not found!" % self.glade_file)
		else:
			print "galde file:", self.glade_file
		
		self.xml = gtk.glade.XML(self.glade_file)
		self.window = self.xml.get_widget("table_editor")
		self.xml.signal_autoconnect(self)
		
		self.treeview = self.xml.get_widget("table_columns")
		self.model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
		self.treeview.set_model(self.model)
		self.treeview.set_headers_clickable(False)
		self.treeview.set_reorderable(True)
		self.treeview.insert_column_with_attributes(-1, "name", gtk.CellRendererText(), text=0)
		self.treeview.insert_column_with_attributes(-1, "type", gtk.CellRendererText(), text=1)
		self.treeview.insert_column_with_attributes(-1, "comment", gtk.CellRendererText(), text=2)
		self.install_popup_item("table_popup", "edit table", self.edit_table)
		self.ignore_changes = True
		
	def cleanup(self):
		for item, menu in self.popup_items:
			menu.remove(item)		
			del item
		self.popup_items = []
		
	def install_popup_item(self, popup_name, item_catpion, callback):
		popup = self.emma.xml.get_widget(popup_name)
		for child in popup.get_children():
			if child.get_child().get_text() == item_catpion:
				print "%s: warning: there already is a menu item called '%s' in '%s'" % (__name__, item_caption, popup_name)
		item = gtk.MenuItem(item_catpion)
		item.connect("activate", callback)
		item.show()
		popup.append(item)
		self.popup_items.append((item, popup)) 
	
	def edit_table(self, menuitem):
		path, column, iter, table = self.emma.get_current_table()
		self.table = table
		tname = self.xml.get_widget("table_name")
		if not tname:
			print "error: table_name-field not found in xml", self.xml
		e = tname.set_text(table.name)
		e = tname.grab_focus()
		e = self.xml.get_widget("table_comment").set_text(table.props[14])
		self.model.clear()
		for name in table.field_order:
			field = table.fields[name]
			comment = self.extract_comment(field[5]) # todo
			self.model.append(row=(field[0], field[1], comment, list(field), field))
		self.xml.get_widget("table_field_properties").set_sensitive(False)
		self.window.show_all()
	
	def parse_type(self, string):
		match = re.search("\(([0-9,]+)\)$", string)
		if not match:
			return string, None
		return string[0:match.start(0)], match.group(1)

	def extract_comment(self, string):
		p = string.find("COMMENT")
		current = split_strings(string)
		for i, c in enumerate(current):
			if c.startswith("comment="):
				return c[len("comment=")+1:-1]
		return ""
		
	def get_field_capabilities(self, ftype):
		global data_type_capabilities
		try:
			return data_type_capabilities[ftype]
		except:
			print "unknwon type", ftype, "guessing all capabilities!"
			return LEN | UNSIGNED | ZERO | BINARY
		
	def set_type_restrictions(self, ftype, capabilities=None):
		if capabilities is None:
			capabilities = self.get_field_capabilities(ftype)
		set = self.set_field
		set("table_field_length_sensitive", capabilities & LEN)
		set("table_field_unsigned_sensitive", capabilities & UNSIGNED)
		set("table_field_binary_sensitive", capabilities & BINARY)
		
	def set_field(self, xml_name, value):
		if xml_name.endswith("_sensitive"):
			xml_name = xml_name[:-len("_sensitive")]
			widget = self.xml.get_widget(xml_name)
			if type(widget) != gtk.CheckButton:
				widget.set_editable(test(value, True, False))
			widget.set_sensitive(test(value, True, False))
			return
		widget = self.xml.get_widget(xml_name)
		if type(widget) == gtk.Entry:
			widget.set_text(str(value))
		elif type(widget) == gtk.CheckButton:
			widget.set_active(value)
		elif type(widget) == gtk.ComboBox:
			model = widget.get_model()
			for i, v in enumerate(model):
				if value in v[0].split(", "):
					widget.set_active(i)
					break
			else:
				print "value", value, "not found in model", model
		else:
			print "unknown type", type(widget)
	def set_current_field(self, field):
		self.ignore_changes = True
		set = self.set_field
		set("table_field_name", field[0])
		ftype, length = self.parse_type(field[1])
		set("table_field_type", ftype)
		if length is None:
			set("table_field_length", "")
		else:
			set("table_field_length", length)
		
		default = not field[4] is None or field[2] == "YES"
		set("table_field_hasdefault", default)
		set("table_field_default_sensitive", default)
		if default:
			set("table_field_default", test(field[4] is None, "NULL", field[4]))
		else:
			set("table_field_default", "")
		set("table_field_notnull", field[2] != "YES")
		set("table_field_comment", self.extract_comment(field[5]))
		set("table_field_isautoincrement", field[5].find("auto_increment") != -1)
		set("table_field_unsigned", field[5].find("unsigned") != -1)
		set("table_field_binary", field[5].find("binary") != -1)
		self.xml.get_widget("table_field_properties").set_sensitive(True)
		self.set_type_restrictions(ftype)
		self.ignore_changes = False
		
	def on_cursor_changed(self, treeview):
		path, column = treeview.get_cursor()
		row = self.model[path]
		self.set_current_field(row[3])
		
	def on_table_field_changed(self, widget):
		if self.ignore_changes:
			return
		def propagate_back(field, row):
			row[0] = field[0] # name
			row[1] = field[1] # type
		def set_extra(name, active):
			current = set(split_strings(row[3][5]))
			if active:
				current.add(name)
			else:
				current.discard(name)
			row[3][5] = " ".join(current)
		
		fname = widget.name
		if fname.startswith("table_"):
			fname = fname[len("table_"):]
		path, column = self.treeview.get_cursor()
		row = self.model[path]
		if fname == "field_name":
			row[3][0] = widget.get_text()
		elif fname == "field_type" or fname == "field_length":
			widget = self.xml.get_widget("table_field_type")
			ftype = widget.get_active_text().split(", ")[0]
			capabilities = self.get_field_capabilities(ftype)
			length = self.xml.get_widget("table_field_length").get_text()
			self.set_type_restrictions(ftype, capabilities)
			if capabilities & LEN and length != "":
				ftype += "(%s)" % length
			row[3][1] = ftype
		elif fname == "field_default":
			row[3][4] = widget.get_text()
		elif fname == "field_hasdefault":
			default = widget.get_active()
			self.set_field("table_field_default_sensitive", default)
			if not default:
				self.set_field("table_field_default", "")
			row[3][4] = test(default, self.xml.get_widget("table_field_default").get_text(), None)
		elif fname == "field_comment":
			current = split_strings(row[3][5])
			for i, c in enumerate(current):
				if c.startswith("comment="):
					del current[i]
					break
			current.append("comment='%s'" % self.table.host.escape(widget.get_text()))
			row[3][5] = " ".join(current)
		elif fname == "field_notnull":
			row[3][2] = test(widget.get_active(), "", "YES")
		elif fname == "field_isautoincrement":
			set_extra("auto_increment", widget.get_active())
		elif fname == "field_unsigned":
			set_extra("unsigned", widget.get_active())
		elif fname == "field_binary":
			set_extra("binary", widget.get_active())
		else:
			print "unknown change in field", fname
		propagate_back(row[3], row)
	
	def on_table_abort(self, *args):
		self.window.hide()
		
	def on_table_apply(self, *args):
		print args
	
	def on_table_apply_and_open(self, *args):
		print args
		
plugin_instance = None	
def plugin_init(emma_instance):
	global plugin_instance
	plugin_instance = table_editor(emma_instance)
	return plugin_instance
	
def plugin_unload():
	global plugin_instance
	plugin_instance.cleanup()
	del plugin_instance
	plugin_instance = None
	gc.collect()
