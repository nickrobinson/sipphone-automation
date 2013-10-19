import robot
import urllib
import urllib2

BEGIN_REQUEST = "<PolycomIPPhone><Data priority=\"Critical\">"
END_REQUEST = "</Data></PolycomIPPhone>"

from robot.libraries.BuiltIn import BuiltIn

class PhoneKeywords(object):
	ROBOT_LIBRARY_SCOPE = 'Global'

	def __init__(self):
		self.phones = {}
		self.builtin = BuiltIn()

	def setup_phone(self, extension, ipaddr, username, password):
		self.phones[extension] = (ipaddr, username, password)
		self.builtin.log("Added Phone")

	def call_number(self, extenson, number):
		URL = BEGIN_REQUEST + "tel:\\" + number + END_REQUEST
		_send_request(self.phones[extension][0], URL)

	def max_volume(self, extension):
		URL = BEGIN_REQUEST + "Key:VolUp" + END_REQUEST
		_send_request(self.phones[extension][0], URL)	

	def press_headset_key(self, extension):
		URL = BEGIN_REQUEST + "Key:Headset" + END_REQUEST
		_send_request(self.phones[extension][0], URL)

	def press_end_call(self, extension):
		URL = BEGIN_REQUEST + "Key:Softkey2" + END_REQUEST
		_send_request(self.phones[extension][0], URL)

	def press_dnd(self, extension):
		URL = BEGIN_REQUEST + "Key:DoNotDisturb" + END_REQUEST
		_send_request(self.phones[extension][0], URL)

	def press_digit(self, extension, digit):
		keyPressed = ""
		if digit == 0:
			keyPressed = "0"
		elif digit == 1:
			keyPressed = "1"
		elif digit == 2:
			keyPressed = "2"
		elif digit == 3:
			keyPressed = "3"
		elif digit == 4:
			keyPressed = "4"
		elif digit == 5:
			keyPressed = "5"
		elif digit == 6:
			keyPressed = "6"
		elif digit == 7:
			keyPressed = "7"
		elif digit == 8:
			keyPressed = "8"
		elif digit == 9:
			keyPressed = "9"

		URL = BEGIN_REQUEST + "Key:DialPad" + keyPressed + END_REQUEST
		_send_request(self.phones[extension][0], URL)

	def _send_request(ipaddr, request):
		headers = { 'Content-Type' : 'application/x-com-polycom-spipx' }
			
