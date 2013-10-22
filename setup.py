#!/usr/bin/env python

from distutils.core import setup

from os.path import abspath, dirname, join
execfile(join(dirname(abspath(__file__)), 'src', 'SipPhoneLibrary', 'version.py'))

DESCRIPTION = """
Robot Framework keyword library for SIP phone automation.
"""[1:-1]


CLASSIFIERS = """
Development Status :: 2 - Pre-Alpha
License :: Public Domain
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Testing
"""[1:-1]

setup(name         = 'sipphone-automation',
      version      = VERSION,
      description  = 'Robot Framework keyword library for SIP phone automation',
      long_description = DESCRIPTION,
      author       = 'Nick Robinson',
      author_email = 'nick@nlrobinson.com',
      url          = 'http://github.com/nickrobinson/sipphone-automation',
      license      = 'Public Domain',
      keywords     = 'robotframework testing test automation sip phones voip',
      platforms    = 'any',
      classifiers  = CLASSIFIERS.splitlines(),
      package_dir  = {'' : 'src'},
      packages     = ['SipPhoneLibrary'],
      package_data = {'SipPhoneLibrary': ['tests/*.txt']},
      install_requires=[
          'robotframework',
      ],
)

""" From now on use this approach

python setup.py sdist upload
git tag -a 1.2.3 -m 'version 1.2.3'
git push --tags"""
