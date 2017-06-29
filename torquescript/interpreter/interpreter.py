"""
	Torque Script interpreter implementation.
"""

import struct
import inspect

import builtins
import tsopcode

class InterpreterError(StandardError):
	pass
													
class InterpreterError(StandardError):
	pass
	
class Interpreter(object):
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
		
		self.object_types = {object_type.__name__.lower(): object_type for object_type in SimObject.get_children_classes()}
		
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