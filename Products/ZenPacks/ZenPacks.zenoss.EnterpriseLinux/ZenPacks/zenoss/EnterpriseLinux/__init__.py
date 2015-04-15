##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


import logging
from sets import Set
import os.path
import Globals
from Products.ZenModel.ZenPack import ZenPackBase
from Products.ZenModel.ZenPackLoader import ZPLObject
from Products.ZenUtils.Utils import monkeypatch

log = logging.getLogger('zen.EnterpriseLinux')

skinsDir = os.path.join(os.path.dirname(__file__), 'skins')
from Products.CMFCore.DirectoryView import registerDirectory
if os.path.isdir(skinsDir):
    registerDirectory(skinsDir, globals())

plugins = ['zenoss.cmd.linux.ifconfig',
           'zenoss.cmd.linux.memory',
           'zenoss.cmd.linux.netstat_an',
           'zenoss.cmd.linux.netstat_rn',
           'zenoss.cmd.linux.process',
           'zenoss.cmd.linux.rpm']
           
def findLinux(dmd):
    return dmd.findChild('Devices/Server/SSH/Linux')

class ZenPack(ZenPackBase):
    
    def install(self, app):
        """
        Add the collector plugins.
        """
        try:
            linux = findLinux(app.dmd)
        except Exception, e:
            import traceback
            log.debug(traceback.format_exc())
            raise Exception('Device class Server/SSH/Linux does not exist. '
                            'Cannot install EnterpriseLinux ZenPack.')
        ZenPackBase.install(self, app)
        newPlugins = linux.zCollectorPlugins
        for plugin in plugins:
            if plugin not in linux.zCollectorPlugins:
                newPlugins.append(plugin)
        linux.setZenProperty('zCollectorPlugins', newPlugins)
        
    def remove(self, app, leaveObjects=False):
        """
        Remove the collector plugins. Load core zenpack's objects.
        """
        ZenPackBase.remove(self, app, leaveObjects)
        linux = findLinux(app.dmd)
        if not leaveObjects:
            linux.zCollectorPlugins = list(
                    Set(linux.zCollectorPlugins) - Set(plugins))
            for zenpack in app.dmd.ZenPackManager.packs():
                if zenpack.id == 'ZenPacks.zenoss.LinuxMonitor':
                    ZPLObject().load(zenpack, app)

from Products.ZenModel.OSProcess import OSProcess
if not hasattr(OSProcess, 'getMinProcessCount'):
    @monkeypatch("Products.ZenModel.OSProcess.OSProcess")
    def getMinProcessCount(self):
        return None

if not hasattr(OSProcess, 'getMaxProcessCount'):
    @monkeypatch("Products.ZenModel.OSProcess.OSProcess")
    def getMaxProcessCount(self):
        return None
