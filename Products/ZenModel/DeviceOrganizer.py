#################################################################
#
#   Copyright (c) 2002 Zenoss, Inc. All rights reserved.
#
#################################################################

__doc__="""DeviceOrganizer

$Id: DeviceOrganizer.py,v 1.6 2004/04/22 19:08:47 edahl Exp $"""

__version__ = "$Revision: 1.6 $"[11:-2]

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from AccessControl import Permissions as permissions

from Organizer import Organizer
from DeviceManagerBase import DeviceManagerBase

class DeviceOrganizer(Organizer, DeviceManagerBase):
    """
    DeviceOrganizer is the base class for device organizers.
    It has lots of methods for rolling up device statistics and information.
    """
    
    security = ClassSecurityInfo()


    # Screen action bindings (and tab definitions)
    factory_type_information = ( 
        { 
            'id'             : 'DeviceGroup',
            'meta_type'      : 'DeviceGroup',
            'description'    : """Base class for all devices""",
            'icon'           : 'DeviceGroup.gif',
            'product'        : 'ZenModel',
            'factory'        : 'manage_addDeviceGroup',
            'immediate_view' : 'deviceOrganizerStatus',
            'actions'        :
            ( 
                { 'id'            : 'status'
                , 'name'          : 'Status'
                , 'action'        : 'deviceOrganizerStatus'
                , 'permissions'   : (
                  permissions.view, )
                },
                { 'id'            : 'events'
                , 'name'          : 'Events'
                , 'action'        : 'viewEvents'
                , 'permissions'   : (
                  permissions.view, )
                },
                { 'id'            : 'historyEvents'
                , 'name'          : 'Archive'
                , 'action'        : 'viewHistoryEvents'
                , 'permissions'   : (
                  permissions.view, )
                },
                { 'id'            : 'viewHistory'
                , 'name'          : 'Changes'
                , 'action'        : 'viewHistory'
                , 'permissions'   : (
                  permissions.view, )
                },
            )
         },
        )


    def getSubDevices(self, devfilter=None, devrel="devices"):
        """get all the devices under and instance of a DeviceGroup"""
        devices = getattr(self, devrel, None)
        if not devices: 
            raise AttributeError, "%s not found on %s" % (devrel, self.id)
        devices = filter(devfilter, devices())
        for subgroup in self.children():
            devices.extend(subgroup.getSubDevices(devfilter, devrel))
        return devices


    def getSubDevicesGen(self, devrel="devices"):
        """get all the devices under and instance of a DeviceGroup"""
        devices = getattr(self, devrel, None)
        if not devices: 
            raise AttributeError, "%s not found on %s" % (devrel, self.id)
        for dev in devices.objectValuesGen():
            yield dev
        for subgroup in self.children():
            for dev in subgroup.getSubDevicesGen(devrel):
                yield dev


    def getMonitoredComponents(self):
        """Return monitored components for devices within this DeviceOrganizer.
        """
        cmps = []
        for dev in self.getSubDevicesGen():
            cmps.extend(dev.getMonitoredComponents())
        return cmps


    def getAllCounts(self, devrel="devices"):
        """Count all devices within a device group and get the
        ping and snmp counts as well"""
        devices = getattr(self, devrel)
        pingStatus = 0
        snmpStatus = 0
        devCount = devices.countObjects()
        for dev in devices():
            if dev.getPingStatusNumber() > 0:
                pingStatus += 1
            if dev.getSnmpStatusNumber() > 0:
                snmpStatus += 1
        counts = [devCount, pingStatus, snmpStatus]
        for group in self.children():
            sc = group.getAllCounts()
            for i in range(3): counts[i] += sc[i]
        return counts


    def countDevices(self, devrel="devices"):
        """count all devices with in a device group"""
        count = self.devices.countObjects()
        for group in self.children():
            count += group.countDevices()
        return count


    def pingStatus(self, devrel="devices"):
        """aggrigate ping status for all devices in this group and below"""
        status = self._status("Ping", devrel)
        for group in self.children():
            status += group.pingStatus()
        return status

    
    def snmpStatus(self, devrel="devices"):
        """aggrigate snmp status for all devices in this group and below"""
        status = self._status("Snmp", devrel)
        for group in self.children():
            status += group.snmpStatus()
        return status

    
    def getEventMatrix(self, severity=1, state=1):
        """Return a list of lists with organizer name and severity rainbow.
        [ "/Email", [['zenevents_5_noack', 1, 3], ['zenevents_4_noack', 0, 4]]]
        """
        matrix = []
        for sys in self.children():
            evtsum = [{"href":sys.getPrimaryUrlPath() + "/viewEvents", 
                     "content": sys.getOrganizerName()}]
            evtsum.extend(sys.getEventSummary())
            matrix.append(evtsum)
        return matrix


    def _status(self, type, devrel="devices"):
        """build status info for device in this device group"""
        status = 0
        statatt = "get%sStatusNumber" % type
        devices = getattr(self, devrel, None)
        if not devices: 
            raise AttributeError, "%s not found on %s" % (devrel, self.id)
        for device in devices():
            if getattr(device, statatt, -1)() > 0:
                status += 1
        return status
    
   
    def statusColor(self, status):
        """colors for status fields for device groups"""
        retval = '#00ff00'
        if status == -1:
            retval = "#d02090"
        elif status == 1:
            retval = '#ffff00'
        elif status == 2:
            retval = '#ff9900'
        elif status > 2:
            retval = '#ff0000'
        return retval


InitializeClass(DeviceOrganizer)

