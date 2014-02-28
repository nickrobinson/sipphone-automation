#!/usr/bin/env python
import urllib2
from xml.dom.minidom import parse, parseString
#from DTMFDetector import *

import robot
from robot.libraries.BuiltIn import BuiltIn
from robot import utils

BEGIN_REQUEST = "<PolycomIPPhone><Data priority=\"Critical\">"
END_REQUEST = "</Data></PolycomIPPhone>"
PUSH_URI = "/push"
POLL_CALL_STATE_URI = "/polling/callstateHandler"
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin'
DEFAULT_PORT = 80
DEFAULT_TIMEOUT = 10 #seconds

class Phone(object):
    def __init__(self, extension, ipaddr, \
        username=DEFAULT_USERNAME, \
        password=DEFAULT_PASSWORD, \
        port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        self.extension = extension
        self.ipaddr = ipaddr
        self.port = port
        url = "http://{0}:{1}{2}"
        self.push_url = url.format(self.ipaddr, self.port, PUSH_URI)
        self.poll_call_state_url = url.format(self.ipaddr, self.port, POLL_CALL_STATE_URI)
        self.username = username
        self.password = password
        self.timeout = timeout
        self.headers = {'Content-Type': 'application/x-com-polycom-spipx'}
        
    def _digest_auth(self, url):
        pwmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwmgr.add_password(None, url, self.username, self.password)
        authhandler = urllib2.HTTPDigestAuthHandler(pwmgr)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
                
    def _send(self, xml_string, url):
        self._digest_auth(url)
        req = urllib2.Request(url=url, data=xml_string, headers=self.headers)
        resp = urllib2.urlopen(req, timeout=self.timeout)
        return resp
        
    def _get(self, url):
        self._digest_auth(url)
        req = urllib2.Request(url=url, headers=self.headers)
        resp = urllib2.urlopen(req, timeout=self.timeout)
        return resp
        
    def send_request(self, xml_string):
        return self._send(xml_string, self.push_url)
    
    def send_poll(self):
        return self._get(self.poll_call_state_url)

class PhoneKeywords(object):
    ROBOT_LIBRARY_SCOPE = 'Global'

    def __init__(self):
        self.phones = {}
        self.builtin = BuiltIn()
        self.root = None
        self.timeout = DEFAULT_TIMEOUT

    def _send_request(self, extension, xml_string):
        """This is a helper function that is responsible for sending the push 
        request to the phone"""
        resp = self.phones[extension].send_request(xml_string)
        if resp.getcode() != 200:
            self.builtin.fail("Result of POST request was not OK")
        
    def _send_poll(self, extension):
        """This is a helper function that is responsible for getting the current
        callstate from the phone"""
        self.root = None
        resp = self.phones[extension].send_poll()
        if resp.getcode() != 200:
            self.builtin.fail("Result of Polling the phone for callstate was not OK")
        else:
            self.root = parseString(resp.read())
            
    def setup_phone(self, extension, ipaddr, \
        username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD, \
        port=str(DEFAULT_PORT), timeout='{0} seconds'.format(DEFAULT_TIMEOUT)):
        """This keyword accepts all parameters neccessary to setup phone storage
        `extension` - The extension number of this phone
        `ipaddr` - The phones IP Address (v4 only for the moment)
        `username` - The phones push URL username. This should be setup in the phones .cfg file
        `password` - The phones push URL password
        `timeout` - Timeout for SIP phone API HTTP requests
        """
        self.phones[extension] = Phone(extension, ipaddr, username, password, \
            port, timeout=utils.timestr_to_secs(timeout))
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

    def press_redial(self, extension):
        """Press the redial key on the phone with the specified extension"""
        URL = BEGIN_REQUEST + "Key:Redial" + END_REQUEST
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
        
    def press_messages(self, extension):
        """Press the Messages key on the phone with the specified extension"""
        URL = BEGIN_REQUEST + "Key:Messages" + END_REQUEST
        self._send_request(extension, URL)

    def expect_connected(self, extension):
        """This function should check that the phone with the provided extension is 
        currently in a connected call"""
        self._send_poll(extension)
        node = self.root.getElementsByTagName('CallState')[0]
        if node.childNodes[0].data != 'Connected':
            self.builtin.fail("Phone call is not currently connected")
    
    def expect_ringback(self, extension):
        """Check to make sure that the phone with the specified extension is hearing ringback"""
        self._send_poll(extension)
	node = self.root.getElementsByTagName('CallState')[0]
        if node.childNodes[0].data != 'RingBack':
            self.builtin.fail("Phone call is not currently getting ringback")

    def expect_call_hold(self, extension):
        """Check to make sure that the phones call is on hold by the other party"""
        self._send_poll(extension)
        node = self.root.getElementsByTagName('CallState')[0]
        if node.childNodes[0].data != 'CallHold':
            self.builtin.fail("Phone call is not currently on hold by the other party")

    def expect_call_held(self, extension):
        """Check to make sure that the phone has placed a call on hold"""
        self._send_poll(extension)
        node = self.root.getElementsByTagName('CallState')[0]
        if node.childNodes[0].data != 'CallHeld':
            self.builtin.fail("Phone call is not currently held by this phone")

    #def expect_dtmf_digits(self, file, digits):
    #    """Check a wav file and verify that the expected digits are heard in the wav file"""
    #    dtmf = DTMFdetector(8000, False);
    #    data = dtmf.getDTMFfromWav(file);
    #    if data != digits:
    #        self.builtin.fail("Digits heard(%s) did not match digits expected(%s)" %(data, digits))

    def expect_caller_id(self, extension, callerid):
        """Check the incoming call caller id for what you expect"""
        self._send_poll(extension)
        node = self.root.getElementsByTagName('CallingPartyName')[0]
        if node.childNodes[0].data != callerid:
            self.builtin.fail("Current Calling party %s does not match expected caller id: %s"%(node[0].nodeValue, callerid))
    
    def get_phone_mac(self, extension):
        """Returns the MAC address of the extension specified"""
        phone_mac = ''
        self._send_poll(extension)
        elems = self.root.getElementsByTagName('MACAddress')
        if len(elems):
            phone_mac = elems[0].childNodes[0].data
        return phone_mac

    def get_phone_model(self, extension):
        """Returns the model number of the phone with the specified extension"""
        phone_model = ''
        self._send_poll(extension)
        elems = self.root.getElementsByTagName('ModelNumber')
        if len(elems):
            phone_model = elems[0].childNodes[0].data
        return phone_model
        
if __name__ == '__main__':
    #unit test
    import time
    ext1 = '1001'
    ext1_ip = '10.17.127.216'
    ext1_port = '8081'
    ext2 = '1002'
    ext2_ip = '10.17.127.216'
    ext2_port = '8082'
    lib = PhoneKeywords()
    
    #setup
    lib.setup_phone(ext1, ext1_ip, port=ext1_port, timeout='5 seconds')
    lib.setup_phone(ext2, ext2_ip, port=ext2_port, timeout='5 seconds')
    
    lib._send_poll(ext1)
    print lib.root.toxml()
    
    #phone model
    model1 = lib.get_phone_model(ext1)
    print 'model1:', model1
    model2 = lib.get_phone_model(ext2)
    print 'model2:', model2
    
    #phone mac
    mac1 = lib.get_phone_mac(ext1)
    print 'macl1:', mac1
    mac2 = lib.get_phone_mac(ext2)
    print 'mac2:', mac2
    
    #press digit
    lib.press_headset_key(ext1)
    for digit in ext2:
        lib.press_digit(ext1, digit)
    time.sleep(2)
    
    lib._send_poll(ext1)
    print lib.root.toxml()
    
    #call_state
    call_state = lib.root.getElementsByTagName('CallState')[0].childNodes[0].data
    print 'call_state:', call_state
    assert call_state == 'RingBack'
    

