"""
	All built in functions.
"""

import sys

def echo(vm):
	"""
		Prints a string to the console.
	"""
	print(vm.stack.pop())
	
def error(vm):
	"""
		Prints an error to the console.
	"""
	print(vm.stack.pop())
	
def vectorAdd(vm):
	"""
		Adds two vectors together.
	"""
	lhs = str(vm.stack.pop()).split()
	rhs = str(vm.stack.pop()).split()
	
	if len(lhs) < 3:
		lhs += [0] * (3 - len(lhs))
	if len(rhs) < 3:
		rhs += [0] * (3 - len(lhs))
		
	vm.stack.append("%f %f %f" % (float(lhs[0]) + float(rhs[0]), float(lhs[1]) + float(rhs[1]), float(lhs[2]) + float(rhs[2])))
	
def quit(vm):
	"""
		Causes an interpreter exit.
	"""
	sys.exit(0)
