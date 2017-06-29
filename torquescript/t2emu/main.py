"""
	Main script for emulating a Tribes 2 console of sorts.
"""

import classes
import builtins

class TorqueScriptCompleter(object):
	options = None
	"""
		A list of possible autocomplete options.
	"""
	
	def __init__(self, options):
		self.options = options

class Application(object):
	def main(self):
		# Attempt to initialize GNU readline for some sweet autocomplete action.
		try:
			import readline
		except ImportError as e:
			print("!!! Failed to configure GNU readline. This probably means you're on Windows. Autocomplete features not available.")
			
		print("Tribes 2 Engine Emulation begin. ")
		print(" ")
		
		
		while True:
			raw_input("> ")
		
if __name__ == "__main__":
	Application().main()