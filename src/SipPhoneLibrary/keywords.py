import robot
import urllib
import urllib2
import json
import requests
from requests.auth import HTTPDigestAuth as digest

BEGIN_REQUEST = "<PolycomIPPhone><Data priority=\"Critical\">"
END_REQUEST = "</Data></PolycomIPPhone>"

END_POLL = "/polling/callstateHandler"

from robot.libraries.BuiltIn import BuiltIn

class PhoneKeywords(object):
	ROBOT_LIBRARY_SCOPE = 'Global'

	def __init__(self):
		self.phones = {}
		self.builtin = BuiltIn()

	def _send_request(self, extension, request):
		"""This is a helper function that is responsible for sending the push request to the phone"""
		headers = { 'Content-Type' : 'application/x-com-polycom-spipx' }
		URL = "http://" + self.phones[extension][0] + "/push"
		data = json.dumps(request)
		auth = digest(self.phones[extension][1], self.phones[extension][2])
		result = requests.post(URL, data=data, headers=headers, auth=auth)
		if(result.status_code != requests.codes.ok):
			#Lets retry once to make sure that we cannot contact the phone
			result = requests.post(URL, data=data, headers=headers, auth=auth)
			if(result.status_code != requests.codes.ok):
				self.builtin.fail("Result of POST request was not OK")

	def _send_poll(self, extension):
		"""This is a helper function that is responsible for getting the current callstate from the phone"""
		headers = { 'Content-Type' : 'application/x-com-polycom-spipx' }
		URL = "http://" + self.phones[extension][0] + END_POLL
		auth = digest(self.phones[extension][1], self.phones[extension][2])
		result = requests.post(URL, headers=headers, auth=auth)
		if(result.status_code != requests.codes.ok):
			#Try to poll the phone one more time before failing
			result = requests.post(URL, headers=headers, auth=auth)
			if(result.status_code != requests.codes.ok):
				self.builtin.fail("Result of Polling the phone for callstate was not a 200 OK")
		else:
			XMLstring=result.text.splitlines()
			
	def setup_phone(self, extension, ipaddr, username, password):
		"""This keyword accepts all parameters neccessary to setup phone storage

		`extension` - The extension number of this phone

		`ipaddr` - The phones IP Address (v4 only for the moment)

		`username` - The phones push URL username. This should be setup in the phones .cfg file
		
		`password` - The phones push URL password
		"""
		self.phones[extension] = (ipaddr, username, password)
		self.builtin.log("Added Phone")

	def call_number(self, extension, number):
		"""Have the phone with the provided extension dial the number passed in"""
		URL = BEGIN_REQUEST + "tel:\\" + number + END_REQUEST
		self._send_request(extension, URL)
		self.builtin.log("Called number" + number)

	def max_volume(self, extension):
		"""Turn up the volume all the way on the phone with the specified extension"""
		for i in range(10):
			URL = BEGIN_REQUEST + "Key:VolUp" + END_REQUEST
			self._send_request(extension, URL)	

	def press_headset_key(self, extension):
		"""Press the headset key on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:Headset" + END_REQUEST
		self._send_request(extension, URL)
		
	def press_handsfree_key(self, extension):
		"""Press the headset key on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:Handsfree" + END_REQUEST
		self._send_request(extension, URL)

	def press_end_call(self, extension):
		"""Press the end call key on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:Softkey2" + END_REQUEST
		self._send_request(extension, URL)
		self.builtin.log("Ended Call")

	def press_dnd(self, extension):
		"""Press the DoNotDisturb key on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:DoNotDisturb" + END_REQUEST
		self._send_request(extension, URL)

	def press_digit(self, extension, digit):
		"""Press the specified digit key on the phone with the specified extension"""
		if digit == "*":
			digit = "Star"
		elif digit == "#":
			digit = "Pound"

		URL = BEGIN_REQUEST + "Key:DialPad" + digit + END_REQUEST
		self._send_request(extension, URL)

	def press_hold(self, extension):
		"""Press the hold key on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:Hold" + END_REQUEST
		self._send_request(extension, URL)

	def mute_mic(self, extension):
		"""Press the mic mute key on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:MicMute" + END_REQUEST
		self._send_request(extension, URL)

	def press_line_key(self, extension, lineNumber):
		"""Press the specified line key number on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:Line" + lineNumber + END_REQUEST
		self._send_request(extension, URL)

	def press_transfer(self, extension):
		"""Press the transfer key on the phone with the specified extension"""
		URL = BEGIN_REQUEST + "Key:Transfer" + lineNumber + END_REQUEST
		self._send_request(extension, URL)

	def expect_connected(self, extension):
		"""This function should check that the phone with the provided extension is 
		currently in a connected call"""
		self._send_poll(extension)

			
