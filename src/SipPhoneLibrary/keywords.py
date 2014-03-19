#!/usr/bin/env python
import urllib2
from xml.dom.minidom import parse, parseString
import time

#from DTMFDetector import *

import robot
from robot.libraries.BuiltIn import BuiltIn
from robot import utils

BEGIN_REQUEST = "<PolycomIPPhone><Data priority=\"Critical\">"
END_REQUEST = "</Data></PolycomIPPhone>"
PUSH_URI = "/push"
POLL_CALL_STATE_URI = "/polling/callstateHandler"
POLL_DEVICE_INFO_URI = "/polling/deviceHandler"
POLL_NETWORK_INFO_URI = "/polling/networkHandler"
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin'
DEFAULT_PORT = 80
DEFAULT_TIMEOUT = 10 #seconds
DEFAULT_DELAY = 0.5 #seconds

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
        self.poll_device_info_url = url.format(self.ipaddr, self.port, POLL_DEVICE_INFO_URI)
        self.poll_network_info_url = url.format(self.ipaddr, self.port, POLL_NETWORK_INFO_URI)
        self.username = username
        self.password = password
        self.timeout = timeout
        self.headers = {'Content-Type': 'application/x-com-polycom-spipx'}
        #determine if phone is reponsive (used by End All Calls)
        self.was_responsive_at_setup = False
        try:
            resp = self.poll_device_info()
            if resp.getcode() == 200:
                self.was_responsive_at_setup = True
            else:
                print 'WARNING: Phone (ext {0}) response ({1}) is not success'\
                    .format(self.extension, resp.getcode())
        except urllib2.URLError:
            print 'WARNING: Phone (ext {0}) is not responsive'.format(self.extension)
        
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
    
    def poll_call_state(self):
        return self._get(self.poll_call_state_url)
        
    def poll_device_info(self):
        return self._get(self.poll_device_info_url)
        
    def poll_network_info(self):
        return self._get(self.poll_network_info_url)

class PhoneKeywords(object):
    ROBOT_LIBRARY_SCOPE = 'Global'

    def __init__(self):
        self.phones = {}
        self.builtin = BuiltIn()
        self.timeout = DEFAULT_TIMEOUT
        
    ##
    # "Private" utility methods:
    ##

    def _send_request(self, extension, xml_string):
        """This is a helper function that is responsible for sending the push 
        request to the phone"""
        resp = self.phones[extension].send_request(xml_string)
        if resp.getcode() != 200:
            self.builtin.fail("Result of POST request was not OK")
        
    def _poll_call_state(self, extension):
        """This is a helper function that is responsible for getting the current
        callstate from the phone"""
        root = None
        resp = self.phones[extension].poll_call_state()
        if resp.getcode() != 200:
            self.builtin.fail("Result of Polling the phone for callstate was not OK")
        else:
            root = parseString(resp.read())
        return root
            
    def _poll_device_info(self, extension):
        """This is a helper function that is responsible for getting the 
        device info from the phone"""
        root = None
        resp = self.phones[extension].poll_device_info()
        if resp.getcode() != 200:
            self.builtin.fail("Result of Polling the phone for device info was not OK")
        else:
            root = parseString(resp.read())
        return root
            
    def _poll_network_info(self, extension):
        """This is a helper function that is responsible for getting the current
        network configuration from the phone"""
        root = None
        resp = self.phones[extension].poll_network_info()
        if resp.getcode() != 200:
            self.builtin.fail("Result of Polling the phone for network info was not OK")
        else:
            root = parseString(resp.read())
        return root
        
    def _get_active_line_and_call_counts(self, extension):
        """Utility function to get the number of lines which are not "Inactive" and
        the number of CallInfo blocks in the call state XML"""
        active_lines = 0
        active_calls = 0
        root = self._poll_call_state(extension)
        call_line_infos = root.getElementsByTagName('CallLineInfo')
        for call_line_info in call_line_infos:
            nodes = call_line_info.getElementsByTagName('LineState')
            if len(nodes) and nodes[0].childNodes[0].data != 'Inactive':
                active_lines += 1
        call_infos = root.getElementsByTagName('CallInfo')
        active_calls += len(call_infos)
        return (active_lines, active_calls)
        
    def _get_end_call_softkey_number(self, extension):
        """Utility function to get the End Call softkey number, based on the phone model"""
        phone_model = self.get_phone_model(extension)
        end_call_softkey_number = 2 # VVX ?
        if phone_model == 'SoundPoint IP 321':
            end_call_softkey_number = 1
        return end_call_softkey_number
        
    def _end_all_calls(self, extension):
        """End all calls and put the phone onhook by pressing the end call softkey 
        until there are no CallInfo blocks in the call state XML and the LineState 
        is 'Inactive' on every line. This keyword is meant to be used by the teardown 
        routine of each test case."""
        MAX_ATTEMPTS = 10
        success = False
        for i in range(MAX_ATTEMPTS):
            active_lines, active_calls = self._get_active_line_and_call_counts(extension)
            if active_lines == 0 and active_calls == 0:
                success = True
                break
            else:
                #try to clear the line(s) and/or call(s)
                self.press_softkey(extension, self._get_end_call_softkey_number(extension))
                time.sleep(DEFAULT_DELAY)
        if not success:
            self.builtin.fail("Failed to reset phone (ext {0})".format(extension))
        
    ##
    # Library Keywords:
    ##
            
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
        phone = Phone(extension, ipaddr, username, password, \
            port, timeout=utils.timestr_to_secs(timeout))
        self.phones[extension] = phone
        msg = "Added Phone -\n"
        msg += "extension: " + phone.extension
        msg += ", ipaddr: " + phone.ipaddr
        msg += ", username: " + phone.username
        msg += ", password: " + phone.password
        msg += ", timeout: {0}".format(phone.timeout)
        msg += ", port: {0}".format(phone.port)
        msg += ", push_url: " + phone.push_url
        self.builtin.log(msg)
        
    ##
    # Data Push Request keywords:
    ##

    def call_number(self, extension, number):
        """Have the phone with the provided extension dial the number passed in"""
        xml_string = BEGIN_REQUEST + "tel:\\" + number + END_REQUEST
        self._send_request(extension, xml_string)
        self.builtin.log("Called number " + number)

    def play_audiofile(self, extension, audiofile_path):
        """Download and play the audio file. 
        (See Web App Developer's Guide for Polycom Phones page 21 for more info)"""
        xml_string = BEGIN_REQUEST + "Play:" + audiofile_path + END_REQUEST
        self._send_request(extension, xml_string)

    def press_volume_up(self, extension):
        """Increase the volume by 1 unit on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:VolUp" + END_REQUEST
        self._send_request(extension, xml_string)
        
    def press_volume_down(self, extension):
        """Decrease the volume by 1 unit on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:VolDown" + END_REQUEST
        self._send_request(extension, xml_string)

    def max_volume(self, extension):
        """Turn up the volume all the way on the phone with the specified extension"""
        for i in range(10):
            self.press_volume_up(extension)
    
    def min_volume(self, extension):
        """Turn down the volume all the way on the phone with the specified extension"""
        for i in range(10):
            self.press_volume_down(extension)

    def press_headset_key(self, extension):
        """Press the headset key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:Headset" + END_REQUEST
        self._send_request(extension, xml_string)
        
    def press_handsfree_key(self, extension):
        """Press the headset key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:Handsfree" + END_REQUEST
        self._send_request(extension, xml_string)

    def press_end_call(self, extension):
        """Press the 'End Call' softkey on the phone with the specified extension."""
        self.press_softkey(extension, self._get_end_call_softkey_number(extension))
    
    def end_all_calls(self, extension='*'):
        """End all calls and put the phone onhook by pressing the end call softkey 
        until there are no CallInfo blocks in the call state XML and the LineState 
        is 'Inactive' on every line. This keyword is meant to be used by the teardown 
        routine of each test case.
        extension: '*' (default) means end all calls on all responsive phones."""
        if extension == '*':
            for extension, phone in self.phones.items():
                if phone.was_responsive_at_setup:
                    self._end_all_calls(extension)
                    time.sleep(DEFAULT_DELAY)
                #don't worry about ending calls for phones that were not responsive at setup.
                #because those phones won't have any active calls anyway.
                #Reasoning: Users should be able to "Setup" phones that don't actually exist,
                #doing so should not cause any test failures, only "Expect ..." keywords should
                #cause test failures.
        else:
            self._end_all_calls(extension)
            
    def press_softkey(self, extension, softkey_number):
        """Press the specified softkey. Note: The function of the softkey is dependent
        on the phone configuration. Valid range varies per phone, 1-5 is typical."""
        xml_string = BEGIN_REQUEST + "Key:Softkey{0}".format(softkey_number) + END_REQUEST
        self._send_request(extension, xml_string)

    def press_dnd(self, extension):
        """Press the DoNotDisturb key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:DoNotDisturb" + END_REQUEST
        self._send_request(extension, xml_string)

    def press_digit(self, extension, digit):
        """Press the specified digit key on the phone with the specified extension"""
        if digit == "*":
            digit = "Star"
        elif digit == "#":
            digit = "Pound"
        xml_string = BEGIN_REQUEST + "Key:DialPad" + digit + END_REQUEST
        self._send_request(extension, xml_string)

    def press_hold(self, extension):
        """Press the hold key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:Hold" + END_REQUEST
        self._send_request(extension, xml_string)

    def press_redial(self, extension):
        """Press the redial key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:Redial" + END_REQUEST
        self._send_request(extension, xml_string)
        
    def press_mute(self, extension):
        """Press the mic mute key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:MicMute" + END_REQUEST
        self._send_request(extension, xml_string)
    
    def mute_mic(self, extension):
        """*DEPRECATED* Use keyword `Press Mute` instead"""
        self.press_mute(extension)

    def press_line_key(self, extension, line_number):
        """Press the specified line key number on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:Line{0}".format(line_number) + END_REQUEST
        self._send_request(extension, xml_string)

    def press_transfer(self, extension):
        """Press the transfer key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:Transfer" + END_REQUEST
        self._send_request(extension, xml_string)
        
    def press_messages(self, extension):
        """Press the Messages key on the phone with the specified extension"""
        xml_string = BEGIN_REQUEST + "Key:Messages" + END_REQUEST
        self._send_request(extension, xml_string)
                
    ## Call Line Information XML look like this:
    #<PolycomIPPhone>
    #<CallLineInfo>
    #<LineKeyNum>1</LineKeyNum>
    #<LineDirNum>1001</LineDirNum>
    #<LineState>Active</LineState>
    #<CallInfo>
    #<CallReference>957276f0</CallReference>
    #<CallState>RingBack</CallState>
    #<CallType>Outgoing</CallType>
    #<UIAppearanceIndex>1*</UIAppearanceIndex>
    #<CalledPartyName>1002</CalledPartyName>
    #<CalledPartyDirNum>sip:1002@192.168.0.1</CalledPartyDirNum>
    #<CallingPartyName>Alfred Atkinson</CallingPartyName>
    #<CallingPartyDirNum>sip:1001@192.168.0.1</CallingPartyDirNum>
    #<CallDuration>0</CallDuration>
    #</CallInfo>
    #</CallLineInfo>
    #</PolycomIPPhone>
    ## Call Line Information keywords:

    def get_line_state(self, extension, line='1'):
        """Gets the line state for the specified line.
        Possible values: 'Inactive' or 'Active'."""
        line_state = ''
        root = self._poll_call_state(extension)
        call_line_infos = root.getElementsByTagName('CallLineInfo')
        for call_line_info in call_line_infos:
            nodes = call_line_info.getElementsByTagName('LineKeyNum')
            if len(nodes) and nodes[0].childNodes[0].data == str(line):
                nodes = call_line_info.getElementsByTagName('LineState')
                if len(nodes):
                    line_state = nodes[0].childNodes[0].data
        return line_state
        
    def expect_idle(self, extension):
        """This function should check that the phone with the provided extension is
        currently idle (no calls, line state of every line is 'Inactive')"""
        active_lines, active_calls = self._get_active_line_and_call_counts(extension)
        if active_lines != 0 or active_calls != 0:
            self.builtin.fail("Phone is not currently idle. active_lines={0} active_calls={0}" \
                .format(active_lines, active_calls))

    def expect_connected(self, extension):
        """This function should check that the phone with the provided extension is 
        currently in a connected call"""
        root = self._poll_call_state(extension)
        nodes = root.getElementsByTagName('CallState')
        if len(nodes) and nodes[0].childNodes[0].data == 'Connected':
            pass
        else:
            self.builtin.fail("Phone call is not currently connected\nxml:\n{0}" \
                .format(root.toxml()))
    
    def expect_ringback(self, extension):
        """Check to make sure that the phone with the specified extension is hearing ringback"""
        root = self._poll_call_state(extension)
        nodes = root.getElementsByTagName('CallState')
        if len(nodes) and nodes[0].childNodes[0].data == 'RingBack':
            pass
        else:
            self.builtin.fail("Phone call is not currently getting ringback\nxml:\n{0}" \
                .format(root.toxml()))

    def expect_call_hold(self, extension):
        """Check to make sure that the phones call is on hold by the other party"""
        root = self._poll_call_state(extension)
        nodes = root.getElementsByTagName('CallState')
        if len(nodes) and nodes[0].childNodes[0].data == 'CallHold':
            pass
        else:
            self.builtin.fail("Phone call is not currently on hold by the other party\nxml:\n{0}" \
                .format(root.toxml()))

    def expect_call_held(self, extension):
        """Check to make sure that the phone has placed a call on hold"""
        root = self._poll_call_state(extension)
        nodes = root.getElementsByTagName('CallState')
        if len(nodes) and nodes[0].childNodes[0].data == 'CallHeld':
            pass
        else:
            self.builtin.fail("Phone call is not currently held by this phone\nxml:\n{0}" \
                .format(root.toxml()))

    def expect_caller_id(self, extension, callerid):
        """Check the incoming call caller id for what you expect"""
        success = False
        root = self._poll_call_state(extension)
        nodes = root.getElementsByTagName('CallingPartyName')
        calling_party = ''
        if len(nodes):
            calling_party = nodes[0].childNodes[0].data
            if calling_party == callerid:
                success = True
        if not success:
            self.builtin.fail("Current Calling party ({0}) does not match expected caller id ({1})\nxml:\n{2}" \
                .format(calling_party, callerid, root.toxml()))
    
    ## Device Information XML look like this:
    #<PolycomIPPhone>
    #<DeviceInformation>
    #<MACAddress>0004f2a76cd5</MACAddress>
    #<PhoneDN>Line1:1001</PhoneDN>
    #<AppLoadID>4.0.4.2906 17-Apr-13 23:30</AppLoadID>
    #<UpdaterID>4.4.0.0080</UpdaterID>
    #<ModelNumber>SoundPoint IP 321</ModelNumber>
    #<TimeStamp>2014-02-28T13:27:02-06:00</TimeStamp>
    #</DeviceInformation>
    #</PolycomIPPhone>
    ## Device Information keywords:
    
    def get_mac(self, extension):
        """Returns the MAC address of the extension specified"""
        phone_mac = ''
        root = self._poll_device_info(extension)
        nodes = root.getElementsByTagName('MACAddress')
        if len(nodes):
            phone_mac = nodes[0].childNodes[0].data
        return phone_mac

    def get_phone_model(self, extension):
        """Returns the model number of the phone with the specified extension"""
        phone_model = ''
        root = self._poll_device_info(extension)
        nodes = root.getElementsByTagName('ModelNumber')
        if len(nodes):
            phone_model = nodes[0].childNodes[0].data
        return phone_model
        
    ## Network Information XML look like this:
    #<PolycomIPPhone>
    #<NetworkConfiguration>
    #<DHCPServer>192.168.0.1</DHCPServer>
    #<MACAddress>0004f2a76cd5</MACAddress>
    #<DNSSuffix/>
    #<IPAddress>192.168.0.2</IPAddress>
    #<SubnetMask>255.255.255.0</SubnetMask>
    #<ProvServer>10.17.127.251/Polycom/</ProvServer>
    #<DefaultRouter>192.168.0.1</DefaultRouter>
    #<DNSServer1>192.168.0.1</DNSServer1>
    #<DNSServer2>0.0.0.0</DNSServer2>
    #<VLANID/>
    #<DHCPEnabled>Yes</DHCPEnabled>
    #</NetworkConfiguration>
    #</PolycomIPPhone>
    ## Network Information keywords:
    
    def get_ip_addr(self, extension):
        """Returns the IP address of the phone with the specified extension"""
        ip_addr = ''
        root = self._poll_network_info(extension)
        nodes = root.getElementsByTagName('IPAddress')
        if len(nodes):
            ip_addr = nodes[0].childNodes[0].data
        return ip_addr
        
    def get_prov_server(self, extension):
        """Returns the provisioning server of the phone with the specified extension"""
        prov_server = ''
        root = self._poll_network_info(extension)
        nodes = root.getElementsByTagName('ProvServer')
        if len(nodes):
            prov_server = nodes[0].childNodes[0].data
        return prov_server
        
    def get_dhcp_enabled(self, extension):
        """Returns True if DHCP is enabled on the phone with the specified extension"""
        dhcp_enabled = ''
        root = self._poll_network_info(extension)
        nodes = root.getElementsByTagName('DHCPEnabled')
        if len(nodes):
            dhcp_enabled = nodes[0].childNodes[0].data
        return dhcp_enabled == 'Yes'
    
    def expect_dhcp_enabled(self, extension):
        """Expects DHCP to be enabled on the phone with the specified extension"""
        dhcp_enabled = self.get_dhcp_enabled(extension)
        if not dhcp_enabled:
            self.builtin.fail("DHCP is disabled")
            
    def expect_dhcp_disabled(self, extension):
        """Expects DHCP to be disabled on the phone with the specified extension"""
        dhcp_enabled = self.get_dhcp_enabled(extension)
        if dhcp_enabled:
            self.builtin.fail("DHCP is enabled")
        
    ##
    # DTMF Detection keywords
    ##
        
    #def expect_dtmf_digits(self, file, digits):
    #    """Check a wav file and verify that the expected digits are heard in the wav file"""
    #    dtmf = DTMFdetector(8000, False);
    #    data = dtmf.getDTMFfromWav(file);
    #    if data != digits:
    #        self.builtin.fail("Digits heard(%s) did not match digits expected(%s)" %(data, digits))

