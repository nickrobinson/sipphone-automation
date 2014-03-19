#!/usr/bin/env python
import unittest
import keywords
import time
from keywords_test_parameters import *
from urllib2 import URLError

class TestKeywordsWithTwoPhones(unittest.TestCase):
    """Test Case which requires two phones."""
    def setUp(self):
        #init library
        self.lib = keywords.PhoneKeywords()
        
        #setup
        self.ext1 = phone1['extension']
        self.ext2 = phone2['extension']
        self.lib.setup_phone(self.ext1, phone1['ipaddr'], port=phone1['port'], timeout=phone1['timeout'])
        self.lib.setup_phone(self.ext2, phone2['ipaddr'], port=phone2['port'], timeout=phone2['timeout'])
                
    def test_press_volume_down(self):
        #volume
        self.lib.press_volume_down(self.ext1)
        self.lib.press_volume_down(self.ext2)
        time.sleep(2)
        
    def test_get_dhcp_enabled(self):
        #dhcp
        dhcp_enabled = self.lib.get_dhcp_enabled(self.ext1)
        print 'dhcp_enabled:', dhcp_enabled
        
    def test_get_phone_model(self):
        #phone model
        model1 = self.lib.get_phone_model(self.ext1)
        self.assertTrue(model1 == phone1['model'])
        model2 = self.lib.get_phone_model(self.ext2)
        self.assertTrue(model2 == phone2['model'])
        
    def test_get_phone_mac(self):
        #phone mac
        mac1 = self.lib.get_mac(self.ext1)
        assert mac1 == phone1['mac']
        mac2 = self.lib.get_mac(self.ext2)
        self.assertTrue(mac2 == phone2['mac'])
        
    def test_get_ip_addr(self):
        #phone ip addr
        #(if phones are behind a firewall, this will be different from phone['ipaddr'])
        ip_addr1 = self.lib.get_ip_addr(self.ext1)
        print 'ip_addr1:', ip_addr1
        self.assertTrue(len(ip_addr1.split('.')) == 4)
        ip_addr2 = self.lib.get_ip_addr(self.ext2)
        print 'ip_addr2:', ip_addr2
        self.assertTrue(len(ip_addr1.split('.')) == 4)
        
    def test_get_prov_server(self):
        #phone prov server
        prov_server1 = self.lib.get_prov_server(self.ext1)
        print 'prov_server1:', prov_server1
        prov_server2 = self.lib.get_prov_server(self.ext2)
        print 'prov_server2:', prov_server2
        
    def test_call_scenario_1(self):
        #verify that line 1 is inactive
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Inactive")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Inactive")
        
        #press digit
        self.lib.press_headset_key(self.ext1)
        for digit in self.ext2:
            self.lib.press_digit(self.ext1, digit)
        time.sleep(3)
        #answer
        self.lib.press_headset_key(self.ext2)
        
        root = self.lib._poll_call_state(self.ext1)
        print 'call_state1:'
        print root.toxml()
        
        #verify that line is active
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Active")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Active")
        
        #call_state
        call_state = root.getElementsByTagName('CallState')[0].childNodes[0].data
        self.assertTrue(call_state == 'RingBack')
        self.lib.expect_ringback(self.ext1)

        root = self.lib._poll_device_info(self.ext1)
        print 'device_info1:'
        print root.toxml()
        
        root = self.lib._poll_network_info(self.ext1)
        print 'network_info1:'
        print root.toxml()

        #hang up
        self.lib.press_headset_key(self.ext2)
        
        time.sleep(2)
        
        #verify that line 1 is inactive
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Inactive")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Inactive")
        
    def test_call_scenario_2(self):
        #verify that line 1 is inactive
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Inactive")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Inactive")
        
        #press digit
        self.lib.press_headset_key(self.ext1)
        for digit in self.ext2:
            self.lib.press_digit(self.ext1, digit)
        time.sleep(3)
        #answer
        self.lib.press_headset_key(self.ext2)
        
        #verify that line is active
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Active")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Active")
        
        #test end_all_calls
        self.lib.end_all_calls(self.ext1)
        self.lib.end_all_calls(self.ext2)
        
        #verify that line 1 is inactive
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Inactive")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Inactive")
        
        #test expect_idle
        self.lib.expect_idle(self.ext1)
        self.lib.expect_idle(self.ext2)

    def test_call_scenario_3(self):
        #test end_all_calls
        self.lib.end_all_calls()
        
        #verify that line 1 is inactive
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Inactive")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Inactive")
        
        #press digit
        self.lib.call_number(self.ext1, self.ext2)
        time.sleep(2)
        #answer
        self.lib.press_handsfree_key(self.ext2)
        
        #verify that line is active
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Active")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Active")
        
        #test press_end_call
        self.lib.press_end_call(self.ext1)
        time.sleep(1)
        
        #verify that line 1 is inactive
        line_state = self.lib.get_line_state(self.ext1)
        self.assertEqual(line_state, "Inactive")
        line_state = self.lib.get_line_state(self.ext2)
        self.assertEqual(line_state, "Inactive")
        
        #test expect_idle
        self.lib.expect_idle(self.ext1)
        self.lib.expect_idle(self.ext2)
        
class TestKeywordsWithUnreachablePhone(unittest.TestCase):
    def setUp(self):
        #init library
        self.lib = keywords.PhoneKeywords()
        
    def test_unreachable_phone(self):
        #setup a bogus phone
        self.lib.setup_phone('0000', 'www.not-used.com', port=999, timeout='1 seconds')
        self.lib.setup_phone('0001', 'www.not-used.com', port=999, timeout='1 seconds')
        
        for ext, phone in self.lib.phones.items():
            self.assertFalse(phone.was_responsive_at_setup)
        
        with self.assertRaises(URLError):
            self.lib.expect_idle('0000')
            
        self.lib.end_all_calls()

if __name__ == '__main__':
    test_classes_to_run = []
    test_classes_to_run.append(TestKeywordsWithTwoPhones)
    test_classes_to_run.append(TestKeywordsWithUnreachablePhone)

    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)

    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)
    
    
