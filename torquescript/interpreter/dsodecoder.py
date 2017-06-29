import struct

import tsopcode

class DecoderError(StandardError):
	pass
				
class DSODecoder(object):
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