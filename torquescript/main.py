"""
	Main script.
"""

import tsinterpreter

class Application(object):
	def main(self):
		block = tsinterpreter.v1.CodeBlock()
		block.string_table.append("1 1 1")
		block.string_table.append("2 3 4")
		block.string_table.append("vectorAdd")
		block.string_table.append("testinline")
		block.string_table.append("ScriptObject")
		block.string_table.append("classname")
		block.string_table.append("FauxName")
		block.string_table.append("echo")
		block.string_table.append("quit")
		
		block.function_table["testinline"] = [
			tsinterpreter.v1.opcodes.PushString([2]),
			tsinterpreter.v1.opcodes.CallFunction(),
			tsinterpreter.v1.opcodes.PushString([4]),
			tsinterpreter.v1.opcodes.PushString([2]),
			tsinterpreter.v1.opcodes.CreateInstance([2]),
			tsinterpreter.v1.opcodes.PushString([5]),
			tsinterpreter.v1.opcodes.PushString([6]),
			tsinterpreter.v1.opcodes.SetMember(),
			tsinterpreter.v1.opcodes.PushString([5]),
			tsinterpreter.v1.opcodes.GetMember(),
			tsinterpreter.v1.opcodes.PushString([7]),
			tsinterpreter.v1.opcodes.CallFunction(),
			tsinterpreter.v1.opcodes.PushString([8]),
			tsinterpreter.v1.opcodes.CallFunction(),
		]
		
		block.function_table["test"] = [
			tsinterpreter.v1.opcodes.PushString([0]),
			tsinterpreter.v1.opcodes.PushString([1]),
			tsinterpreter.v1.opcodes.PushString([3]),
			tsinterpreter.v1.opcodes.CallFunction(),
		]
		
		block.global_code = [
		]
		
		data = block.generate_bytes()
		block = tsinterpreter.CodeBlock(data)
		print(repr(data))
		vm = tsinterpreter.TSInterpreter()
		vm.register_codeblock(block)
		
		# Call the code
		print(vm.call("test"))
		
if __name__ == "__main__":
	Application().main()