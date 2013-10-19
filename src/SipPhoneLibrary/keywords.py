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

	def _send_request(self, extension, request):
		headers = { 'Content-Type' : 'application/x-com-polycom-spipx' }
		URL = "http://" + self.phones[extension][0] + "/push"
		data = json.dumps(request)
		auth = digest(self.phones[extension][1], self.phones[extension][2])
		result = requests.post(URL, auth, verify=False, data, headers)

	def setup_phone(self, extension, ipaddr, username, password):
		self.phones[extension] = (ipaddr, username, password)
		self.builtin.log("Added Phone")

	def call_number(self, extension, number):
		URL = BEGIN_REQUEST + "tel:\\" + number + END_REQUEST
		self._send_request(extension, URL)
		self.builtin.log("Called number" + number)

	def max_volume(self, extension):
		for i in range(10):
			URL = BEGIN_REQUEST + "Key:VolUp" + END_REQUEST
			self._send_request(extension, URL)	

	def press_headset_key(self, extension):
		URL = BEGIN_REQUEST + "Key:Headset" + END_REQUEST
		self._send_request(extension, URL)

	def press_end_call(self, extension):
		URL = BEGIN_REQUEST + "Key:Softkey2" + END_REQUEST
		self._send_request(extension, URL)
		self.builtin.log("Ended Call")

	def press_dnd(self, extension):
		URL = BEGIN_REQUEST + "Key:DoNotDisturb" + END_REQUEST
		self._send_request(extension, URL)

	def press_digit(self, extension, digit):
		if digit == "*":
			digit = "Star"
		elif digit == "#":
			digit = "Pound"

		URL = BEGIN_REQUEST + "Key:DialPad" + digit + END_REQUEST
		self._send_request(extension, URL)

	def press_hold(self, extension):
		URL = BEGIN_REQUEST + "Key:Hold" + END_REQUEST
		self._send_request(extension, URL)

	def mute_mic(self, extension):
		URL = BEGIN_REQUEST + "Key:MicMute" + END_REQUEST
		self._send_request(extension, URL)

	def press_line_key(self, extension, lineNumber):
		URL = BEGIN_REQUEST + "Key:Line" + lineNumber + END_REQUEST
		self._send_request(extension, URL)

	def press_transfer(self, extension):
		URL = BEGIN_REQUEST + "Key:Transfer" + lineNumber + END_REQUEST
		self._send_request(extension, URL)

			
