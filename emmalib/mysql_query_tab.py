import pango

class mysql_query_tab:
	def __init__(self, xml, nb):
		self.xml = xml
		self.nb = nb
		
		renameload = {
			"textview": "query_text", 
			"treeview": "query_view", 
			"add_record": "add_record_tool",
			"delete_record": "delete_record_tool",
			"apply_record": "apply_record_tool",
			"local_search": "local_search_button",
			"remove_order": "remove_order",
			"label": "query_label",
			"page": "first_query",
			"query_bottom_label": "query_bottom_label",
		}
		
		for attribute, xmlname in renameload.iteritems():
			self.__dict__[attribute] = xml.get_widget(xmlname)
			
		self.db = None
		self.model = None
		self.last_source = None
		self.result_info = None
		self.append_iter = None
		if hasattr(self, "query"):
			self.textview.get_buffer().set_text(self.query)

	def __getstate__(self):
		b = self.textview.get_buffer()
		d = {
			"name": self.nb.get_tab_label_text(self.page),
			"query": b.get_text(b.get_start_iter(), b.get_end_iter())
		}
		print "query will pickle:", d
		return d


	def destroy(self):
		# try to free some memory
		if self.model: self.model.clear()
		self.textview.get_buffer().set_text("")
		del self.treeview
		del self.model
		del self.textview
		self.treeview = None
		self.model = None
		self.textview = None
		
	def set(self, text):
		self.last_source = text
		self.textview.get_buffer().set_text(text)
	
	def update_bottom_label(self):
		self.query_bottom_label.set_label("encoding: %s" % self.encoding)
		
	def set_query_encoding(self, encoding):
		self.encoding = encoding
		self.update_bottom_label()
		
	def set_query_font(self, font_name):
		self.textview.get_pango_context()
		fd = pango.FontDescription(font_name)
		self.textview.modify_font(fd)

	def set_result_font(self, font_name):
		self.treeview.get_pango_context()
		fd = pango.FontDescription(font_name)
		self.treeview.modify_font(fd)

	def set_wrap_mode(self, wrap):
		self.textview.set_wrap_mode(wrap)
