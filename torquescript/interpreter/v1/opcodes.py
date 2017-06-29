import struct

import tsinterpreter

class PushString(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a string push operation. The parameter for this opcode is a 2 byte sequence
		representing the string table entry to push.
	"""
	IDENTIFIER = 0x11223344
	
	def read_parameters(self, byte_data, current_offset):
		self.parameters = [struct.unpack_from("<H", byte_data, current_offset)[0]]
		return 2
				
	def generate_bytes(self):
		return struct.pack("<IH", self.IDENTIFIER, self.parameters[0])
		
	def execute(self, vm, code_block):
		vm.stack.append(code_block.string_table[self.parameters[0]])
		
class CreateInstance(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a new object instantiation.
	"""
	IDENTIFIER = 0x6660666
	
	def execute(self, vm, code_block):
		object_name = vm.stack.pop()
		type_name = vm.stack.pop().lower()
		
		if type_name not in vm.object_types:
			print("Attempted to instantiate non-conobject '%s'" % type_name)
			vm.stack.append("")
			return
		
		vm.stack.append(vm.object_types[type_name](vm))
		
class SetMember(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a new object instantiation.
	"""
	IDENTIFIER = 0x103431
	
	def execute(self, vm, code_block):
		rhs = vm.stack.pop()
		lhs = vm.stack.pop()
		target = vm.stack[-1]
		target.set_member(lhs, rhs)
		
class GetMember(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a new object instantiation.
	"""
	IDENTIFIER = 0x102085
	
	def execute(self, vm, code_block):
		rhs = vm.stack.pop()
		lhs = vm.stack.pop()
		vm.stack.append(lhs.get_member(rhs))
		
class PushImmediate(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a push of a constant non-string value.
	"""
	IDENTIFIER = 0x11443344
	
	def read_parameters(self, byte_data, current_offset):
		self.parameters = [struct.unpack_from("<I", byte_data, current_offset)[0]]
		return 4
				
	def generate_bytes(self):
		return struct.pack("<II", self.IDENTIFIER, self.parameters[0])
		
	def execute(self, vm, code_block):
		vm.stack.append(self.parameters[0])
		
class Add(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing an addition operation.
	"""
	IDENTIFIER = 0x44221100
	
	def execute(self, vm, code_block):
		rhs = vm.stack.pop()
		lhs = vm.stack.pop()
		
		# Force floats to better emulate T2 engine behavior
		vm.stack.append(float(rhs) + float(lhs))
		
class CallFunction(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a push of a constant non-string value.
	"""
	IDENTIFIER = 0x345671
						
	def execute(self, vm, code_block):
		function_name = vm.stack.pop()
		vm.stack = vm.call(function_name)
		
class Return(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a return.
	"""
	IDENTIFIER = 0x8675309
						
	def execute(self, vm, code_block):
		vm.return_from_frame()
		
class Subtract(tsinterpreter.tsopcode.OpCode):
	"""
		An opcode representing a subtraction operation.
	"""
	IDENTIFIER = 0x00112233
	
	def execute(self, vm, code_block):
		rhs = vm.stack.pop()
		lhs = vm.stack.pop()
		
		# Force floats to better emulate T2 engine behavior
		vm.stack.append(float(rhs) - float(lhs))