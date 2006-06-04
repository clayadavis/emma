
class table_editor:
	def __init__(self, emma_instance):
		self.emma_instance = emma_instance

def plugin_init(emma_instance):
	return table_editor(emma_instance)
	