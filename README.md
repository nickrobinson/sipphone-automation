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

## Installation
This library has been added to the PyPi package system. Installation is as simple as entering the command below
`pip install sipphone-automation`
