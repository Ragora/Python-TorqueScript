import struct

from dsodecoder import DSODecoder

class CodeBlock(DSODecoder):
	"""
		A class representing a compiled code unit, usable by the TSInterpreter runtime.
	"""
	class Function(object):
		"""
			A class representing a callable code path.
		"""
		
		code = None
		"""
			A list of opcodes to execute for this function.
		"""
		
		def __init__(self, code):
			self.code = code
			
		def call(self, vm, code_block):
			"""
				Executes this function.
				
				:param vm: The intepreter instance to execute within the context of.
				:param code_block: The code block to execute within the context of.
			"""
			for opcode in self.code:
				opcode.execute(vm, code_block)
			
	class DataBlock(object):
		attributes = None
		"""
			A dictionary mapping attribute names to their values. Mapping should always be to integers, floats and strings
			except in cases of when runtime evaluation is necessary in which case we map to a list of opcodes.
		"""
		def __init__(self, attributes={}):
			pass
			
	global_functions = None
	"""
		A dictionary mapping global functions to their function declarations.
	"""
	
	global_code = None
	"""
		Global code data to execute when this codeblock is initialized for a TSInterpreter instance.
	"""
		
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
		
	def call(self, vm):
		"""
			Calls this codeblock which essentially will just execute the code that is declared globally for the script associated with this codeblock.
			
			:param vm: The interpreter instance to execute in the context of.
		"""
		for opcode in self.global_code:
			opcode.execute(vm, self)
			
	def __init__(self, byte_data=None):
		super(CodeBlock, self).__init__(byte_data)
		
		self.global_code = []
		
		if byte_data is not None:
			self.load(byte_data)
			
	def generate_bytes(self):
		return struct.pack("<I", self.VERSION_IDENTIFIER)