##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


import os

from Products.ZenRRD.tests.BaseParsersTestCase import BaseParsersTestCase

from ZenPacks.zenoss.EnterpriseLinux.parsers.linux.ifconfig import ifconfig
from ZenPacks.zenoss.EnterpriseLinux.parsers.linux.diskstats import diskstats


class LinuxParsersTestCase(BaseParsersTestCase):

    def testLinuxParsers(self):
        """
        Test all of the parsers that have test data files in the data
        directory.
        """
        datadir = "%s/parserdata/linux" % os.path.dirname(__file__)

        parserMap = {'/sbin/ifconfig -a': ifconfig,
                     '/bin/cat /proc/diskstats': diskstats,
                     }

        self._testParsers(datadir, parserMap)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(LinuxParsersTestCase))
    return suite
