##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


import os

from Products.DataCollector.tests.BasePluginsTestCase \
        import BasePluginsTestCase

from ZenPacks.zenoss.EnterpriseLinux.modeler.plugins.zenoss.cmd.linux.rpm \
        import rpm

class LinuxPluginsTestCase(BasePluginsTestCase):
    
    
    def runTest(self):
        """
        Test all of the plugins that have test data files in the data
        directory.
        """
        
        Plugins = [rpm]
        datadir = "%s/plugindata/linux" % (os.path.dirname(__file__))
        self._testDataFiles(datadir, Plugins)
        
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(LinuxPluginsTestCase))
    return suite
