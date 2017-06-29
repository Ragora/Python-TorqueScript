from simobject import SimObject

class ScriptObject(SimObject):
	@SimObject.Field
	def classname(instance, value):
		# FIXME: Need to link functions to this script object
		return value
		
	@SimObject.Field
	def superclass(instance, value):
		# FIXME: Need to link functions to this script object
		return value