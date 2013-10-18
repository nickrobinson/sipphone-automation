import robot

from robot.libraries.BuiltIn import BuiltIn

class PhoneKeywords(object):
	ROBOT_LIBRARY_SCOPE = 'Global'

	def __init__(self):
		self.phones = {}
		self.builtin = BuiltIn()

	def setup_phone(self, extension, ipaddr, username, password):
		self.phones[extension] = (ipaddr, username, password)

	
