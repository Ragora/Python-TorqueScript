"""
	Torque Script interpreter implementation.
"""

import struct
import inspect

import builtins
import tsopcode

class InterpreterError(StandardError):
	pass
	
class DecoderError(InterpreterError):
	pass
		
class Decoder(object):
	instructions = None
	string_table = None
	global_code = None
	function_table = None
	
	byte_data = None
	"""
		The raw byte data we are processing.
	"""
	
	byte_index = None
	"""
		The current byte index we are at.
	"""
	
	opcode_table = None
	"""
		The current opcode table.
	"""
	
	def __init__(self, byte_data):
		self.byte_index = 0
		self.byte_data = byte_data
		self.opcode_table = self.get_opcode_table()	
		
		if byte_data is None:
			self.instructions = []
			self.string_table = []
			self.global_code = []
			self.function_table = {}
	
	def get_opcode_table(self):
		"""
			Returns a dictionary mapping opcode identifiers to their opcode metadata.
			
			:rtype: dict
			:return: A dictionary mapping opcode identifiers to opcode metadata.
		"""
		return {opcode.IDENTIFIER: opcode for opcode in tsopcode.OpCode.__subclasses__()}
		
	def read_fixed_bytes(self, type, advance=True, length=None):
		if self.byte_index >= len(self.byte_data):
			raise DecoderError("Attempted out of bounds read!")
			
		if type is int:
			result = struct.unpack_from("<I", self.byte_data, self.byte_index)[0]
			
			if advance is True:
				self.byte_index += 4			
			return result
		else:
			raise DecoderError("Unknown fixed-length data type: %s" % type.__name__) 
		
	def read_variable_bytes(self, type=str, terminator="\x00", advance=True):
		if self.byte_index >= len(self.byte_data):
			raise DecoderError("Attempted out of bounds read!")
					
		terminator_location = self.byte_data.find(terminator, self.byte_index)		
		if terminator_location == -1:
			raise DecoderError("Encountered end-of-file looking for terminator %s" % repr(terminator))
			
		result = type(self.byte_data[self.byte_index:terminator_location])
		if advance is True:
			self.byte_index = terminator_location + 1			
		return result
		
	def read_opcode_bytes(self):
		if self.byte_index >= len(self.byte_data):
			raise DecoderError("Attempted out of bounds read!")
			
		current_identifier = struct.unpack_from("<I", self.byte_data, self.byte_index)[0]
		
		# If this does not correspond to an opcode, we probably encountered in a format byte.
		if current_identifier not in self.opcode_table:
			return None
						
		generated_opcode = self.opcode_table[current_identifier]()
		
		# Advance the byte counter
		# FIXME: Magic number 4, opcode length
		self.byte_index += generated_opcode.read_parameters(self.byte_data, self.byte_index + 4) + 4
		return generated_opcode
		
	def generate_bytes(self):
		raise NotImplementedError("No encoder built.")
										
class CodeBlock(Decoder):
	def load(self, byte_data):
		# Initialize from a file handle
		if type(byte_data) is file:
			byte_data = byte_data.read()
		
		version_handlers = self.get_versions()
		version_identifier = self.read_fixed_bytes(int)
		if version_identifier not in version_handlers:
			raise DecoderError("Unknown compiled file version: %s" % hex(version_identifier))
		
		# Once we know the handler, we become that handler.
		self.__class__ = version_handlers[version_identifier]
		self.load(byte_data)
	
	def get_versions(self):
		return {codeblock_handler.VERSION_IDENTIFIER: codeblock_handler for codeblock_handler in CodeBlock.__subclasses__()}
		
	def __init__(self, byte_data=None):
		super(CodeBlock, self).__init__(byte_data)
		
		if byte_data is not None:
			self.load(byte_data)
			
	def generate_bytes(self):
		return struct.pack("<I", self.VERSION_IDENTIFIER)
				
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
		
class ScriptObject(SimObject):
	@SimObject.Field
	def classname(instance, value):
		# FIXME: Need to link functions to this script object
		return value
		
	@SimObject.Field
	def superclass(instance, value):
		# FIXME: Need to link functions to this script object
		return value
	
class InterpreterError(StandardError):
	pass
	
class TSInterpreter(object):
	current_identifier_counter = None
	
	global_functions = None
	
	stack = None
	"""
		The current virtual machine stack.
	"""
	
	code_blocks = None
	
	builtin_functions = None

	def __init__(self):
		self.stack = []
		self.code_blocks = {}
		self.global_functions = {}
		self.current_identifier_counter = 0
		self.builtin_functions = {current_member[1].__name__: current_member[1] for current_member in inspect.getmembers(builtins, inspect.isfunction)}
		self.object_types = {base_class.__name__.lower(): base_class for base_class in SimObject.__subclasses__()}
		
	def get_next_identifier(self):
		self.current_identifier_counter += 1
		return self.current_identifier_counter
		
	def register_codeblock(self, block):
		# Update the function table
		for function_name, function_code in zip(block.function_table.keys(), block.function_table.values()):
			self.global_functions[function_name] = function_code
			self.code_blocks[function_name] = block
			
		# Execute any global code it has
		for opcode in block.global_code:
			opcode.execute(self, block)
	
	def call(self, function_name, target=None):
		# FIXME: Code blocks shouldn't override built ins unless package hooked?
		if function_name not in self.global_functions:
			# Look for a built in by this name
			if function_name not in self.builtin_functions:
				print("Warning: Attempted to call non-existent function '%s'" % function_name)
				return [""]
			self.builtin_functions[function_name](self)	
		else:
			function_block = self.global_functions[function_name]
			for opcode in function_block:
				opcode.execute(self, self.code_blocks[function_name])
				
		result = self.stack
		self.stack = []
		return result