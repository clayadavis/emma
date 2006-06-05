import os
import sys
import time
import gtk.glade
import gobject
import pprint
pp = pprint.PrettyPrinter()

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
		self.model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
		self.treeview.set_model(self.model)
		#self.treeview.set_headers_clickable(False)
		#self.treeview.set_reorderable(True)
		self.treeview.append_column(gtk.TreeViewColumn("name"))
		self.treeview.append_column(gtk.TreeViewColumn("type"))
		self.treeview.append_column(gtk.TreeViewColumn("comment"))
		
		self.install_popup_item("table_popup", "edit table", self.edit_table)
		
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
		
		e = self.xml.get_widget("table_name").set_text(table.name)
		e = self.xml.get_widget("table_comment").set_text(table.props[14])
		
		#pp.pprint(table.__dict__)
		for name, field in table.fields.iteritems():
			comment = field[2] # todo
			row = (field[0], field[1], comment, field)
			self.model.append(row=row)
		
		self.window.show()
	
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
