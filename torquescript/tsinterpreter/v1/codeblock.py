import struct

import tsinterpreter

class CodeBlock(tsinterpreter.CodeBlock):
	STRING_TABLE_TERMINATOR = 0xcab
	CODE_BLOCK_BEGIN = 0x12345678
	CODE_BLOCK_END = 0xabcdef
	VERSION_IDENTIFIER = 0xdeadbeef
	
	def load(self, byte_data):		
		string_table_entry_count = self.read_fixed_bytes(int)

		# Load the string table
		string_table_start = self.byte_data.find(struct.pack("<I", self.STRING_TABLE_TERMINATOR)[0], self.byte_index)
		if string_table_start == -1:
			raise tsinterpreter.DecoderError("Failed to load string table: Discovered EOF before terminator.")
			
		# FIXME: Technically this allow multiple trailing NULL bytes to be valid
		string_table_data = self.byte_data[self.byte_index:string_table_start].rstrip("\x00").split("\x00")
		
		if len(string_table_data) != string_table_entry_count:
			raise tsinterpreter.DecoderError("Failed to load string table: Expected %u entries. Found %u." % (string_table_entry_count, len(string_table_data)))
		self.string_table = string_table_data
		
		# Read over the string table
		self.byte_index = string_table_start + 4

		# Begin loading code bytes 
		self.global_code = []
		self.function_table = {}

		current_function = None
		while self.byte_index < len(self.byte_data):
			current_opcode = self.read_opcode_bytes()
			current_opcode = current_opcode if current_opcode is not None else self.read_fixed_bytes(int)
			
			# Encountered a code block begin
			if type(current_opcode) is int and current_opcode == self.CODE_BLOCK_BEGIN:
				current_function = self.read_variable_bytes().lower()
				if current_function in self.function_table:
					raise DecoderError("Encountered function '%s' declared multiple times." % current_function)
				self.function_table[current_function] = []
			# Encountered a code block end
			elif type(current_opcode) is int and current_opcode == self.CODE_BLOCK_END:
				current_function = None
			# Encountered an opcode with no current function.
			elif type(current_opcode) in tsinterpreter.tsopcode.OpCode.__subclasses__() and current_function is None:
				self.global_code.append(current_opcode)
			# Encountered an opcode with a function.
			elif type(current_opcode) in tsinterpreter.tsopcode.OpCode.__subclasses__() and current_function is not None:			
				self.function_table[current_function].append(current_opcode)
			else:
				raise tsinterpreter.DecoderError("Encountered unknown opcode at %s: %s." % (hex(self.byte_index), hex(current_opcode)))
				
	def generate_bytes(self):
		result = super(CodeBlock, self).generate_bytes()
		result += struct.pack("<I", len(self.string_table))
		
		# Dump the string table
		for string_table_entry in self.string_table:
			result += "%s\x00" % string_table_entry
		result += struct.pack("<I", self.STRING_TABLE_TERMINATOR)
		
		# Dump global code first
		for global_code_entry in self.global_code:
			result += global_code_entry.generate_bytes()
			
		# Then functions
		for function_name, function_code in zip(self.function_table.keys(), self.function_table.values()):
			result += struct.pack("<I", self.CODE_BLOCK_BEGIN)
			result += "%s\x00" % function_name
			
			for function_code_entry in function_code:
				result += function_code_entry.generate_bytes()	
			result += struct.pack("<I", self.CODE_BLOCK_END)
		return result