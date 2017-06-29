import struct

class OpCode(object):
	"""
		A class representing an opcode. All opcode identifiers are 2 bytes wide with variable length parameters
		which is handled on a per opcode basis.
	"""
	
	IDENTIFIER = None
	"""
		The identifier for this opcode. It must be a list with two integers representing the two bytes making up
		the instruction identifier.
	"""
	
	parameters = None
	"""
		A list of parameters associated with this opcode.
	"""
	
	def __init__(self, parameters=[]):
		self.parameters = parameters
	
	def read_parameters(self, byte_data, current_offset):
		"""
			A function to read parameter data for this opcode from the remaining byte data.
			
			:return: An integer representing the number of bytes ingested from byte_data.
			:rtype: int
		"""
		return 0
				
	def generate_bytes(self):
		"""
			Generates the bytecode necessary for storing this opcode in a format to deserialize from later.
		"""
		return struct.pack("<I", self.IDENTIFIER)