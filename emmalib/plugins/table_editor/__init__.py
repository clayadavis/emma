import os
import sys
import time
import gtk.glade

class table_editor:
	def __init__(self, emma_instance):
		self.emma = emma_instance
		self.popup_items = []
		
		self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
		self.glade_file = os.path.join(self.plugin_dir, "table_editor.glade")
		if not os.access(self.glade_file, os.R_OK):
			raise ValueError("galde file %s not found!" % self.glade_file)
		
		self.xml = gtk.glade.XML(self.glade_file)
		self.window = self.xml.get_widget("table_editor")
		self.xml.signal_autoconnect(self)
		
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
		print "edit table!"
		path, column, iter, table = self.emma.get_current_table()
		print table, table.__dict__
	
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
