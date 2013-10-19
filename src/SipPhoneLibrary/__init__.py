from keywords import PhoneKeywords
from version import VERSION

_version_ = VERSION


class SipPhoneLibrary(PhoneKeywords):
    """ SipPhoneLibrary is a testing tool for Polycom phones to allow
	for automation of calls and verifiation of state. This library works
	best on phones running 4.0.x or newer firmware. Please make sure you
	have enabled the microbrowser push capability in your sip.cfg


        Examples:
        | Setup Phone | 1001 | 10.10.10.2 | admin | admin
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
