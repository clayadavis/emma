
class mysql_query_tab:
	def __init__(self, xml):
		self.xml = xml
		
		renameload = {
			"textview": "query_text", 
			"treeview": "query_view", 
			"add_record": "add_record_tool",
			"delete_record": "delete_record_tool",
			"apply_record": "apply_record_tool",
			"local_search": "local_search_button",
			"remove_order": "remove_order",
			"label": "query_label"
		}
		
		for attribute, xmlname in renameload.iteritems():
			self.__dict__[attribute] = xml.get_widget(xmlname)
			
		self.db = None
		self.model = None
		self.last_source = None
		self.result_info = None
		self.append_iter = None
	def set(self, text):
		self.last_source = text
		self.textview.get_buffer().set_text(text)
	