class SimObject(object):
	identifier = None
	"""
		The identifier of this sim object.
	"""
	
	virtual_machine = None
	"""
		The virtual machine instance we are associated with.
	"""
	
	attributes = None
	"""
		Script defined attributes.
	"""
	
	fields = None
	"""
		Class specific fields.
	"""
	
	class Field(object):
		internal_callable = None
		"""
			The internal python object referenced by this field.
		"""
		
		internal_value = None
		"""
			The internally stored value.
		"""
		
		def __init__(self, callable):
			self.internal_callable = callable
			
		def __set__(self, instance, value):
			self.internal_value = self.internal_callable(instance, value)
			
		def __get__(self, instance, owner):
			return self.internal_value
			
	class Function(object):
		internal_callable = None
		"""
			The internal python object referenced by this field.
		"""
		
		def __init__(self, callable):
			self.internal_callable = callable
		
		def __get__(self, instance, owner):
			return self.internal_callable
			
	@Function
	def delete(self, *params):
		"""
			Deletes this object from the interpreter.
		"""
			
	def __init__(self, vm):
		self.attributes = {}
		self.virtual_machine = vm
		self.identifier = vm.get_next_identifier()
		self.fields = {field_name: field for field_name, field in zip(self.__class__.__dict__.keys(), self.__class__.__dict__.values()) if type(field) is SimObject.Field}
		self.functions = {function_name: function for function_name, function in zip(self.__class__.__dict__.keys(), self.__class__.__dict__.values()) if type(function) is SimObject.Function}
		
	def get_member(self, member_name):
		if member_name in self.fields:
			return getattr(self, member_name)
		elif member_name in self.attributes:
			return self.attributes[member_name]
		return ""
		
	def set_member(self, member_name, value):
		if member_name in self.fields:
			setattr(self, member_name, value)
		elif member_name in self.attributes:
			self.attributes[member_name] = value
		
	def call(self, function_name):
		self.virtual_machine.call(function_name, target=self)
		
	@staticmethod
	def get_children_classes(object_type_list=None):
		if object_type_list is None:
			object_type_list = SimObject.__subclasses__()
			
		"""
			Helper function to recurse the class hierarchy from SimObject downwards.
			
			:param object_type_list: The current type list we are processing.
		"""
		result = object_type_list
		for object_type in object_type_list:
			sub_object_types = object_type.__subclasses__()
			result += sub_object_types + recurse_object_types(sub_object_types)
		return result

	def get_hierarchy(self):
		def recurse_parents(object_type_list=None):
			if object_type_list is None:
				object_type_list = SimObject.__subclasses__()
				
			"""
				Helper function to recurse the class hierarchy from SimObject downwards.
				
				:param object_type_list: The current type list we are processing.
			"""
			result = object_type_list
			for object_type in object_type_list:
				sub_object_types = object_type.__bases__()
				result += sub_object_types + recurse_object_types(sub_object_types)
			return result 
		return recurse_parents(self.__class__.__bases__())