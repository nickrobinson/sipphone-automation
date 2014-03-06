[![Build Status](https://travis-ci.org/nickrobinson/sipphone-automation.png?branch=master)](https://travis-ci.org/nickrobinson/sipphone-automation)

sipphone-automation
===================

Robot Framework library for testing SIP Phones

To run this library you must currently have a Polycom phone running firmware that supports the Microbrowser that 
Polycom provides.

## Polycom Config File
In order for your Polycom phones to support this test you must add the following settings to one of the phones cfg files.
- apps.push.messageType=5
- apps.push.username=bob
- apps.push.password=1234
- apps.statePolling.password="admin"
- apps.statePolling.username="admin"
- apps.statePolling.responseMode="0"
- tone.dtmf.rfc2833Control="0" (This is if you want support for audio detection)

Below is a better example of this
```
<?xml version="1.0" standalone="yes"?>
<localcfg>
<apps apps.statePolling.password="admin" apps.statePolling.username="admin" apps.statePolling.responseMode="0" apps.push.messageType="5" apps.push.username="admin" apps.push.password="admin" apps.push.serverRootURL="http://10.10.10.1"/>
</localcfg>
```

Polycom Documentation is available [here](http://www.polycom.com/content/dam/polycom/common/documents/guides/spip-ssip-vvx-developers-qrg-enus.pdf)

## Installation
This library has been added to the PyPi package system. Installation is as simple as entering the command below

`pip install sipphone-automation`

## Keyword Documentation

Available [here](http://nickrobinson.github.io/SipPhoneLibrary.html)
