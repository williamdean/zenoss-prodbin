##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


"""
A command parser.
    
    Command: 
        
        ifconfig -a
        
        
    Datapoints: 
        
        ifInPackets, ifInErrors, ifOutPackets, ifOutErrors, ifInOctets, 
        ifOutOctets
        
        
    Example command output:
        
        eth0      Link encap:Ethernet  HWaddr 00:0C:29:96:8A:0F
        ...
                  RX packets:15305 errors:0 dropped:0 overruns:0 frame:0
                  TX packets:12843 errors:0 dropped:0 overruns:0 carrier:0
                  collisions:0 txqueuelen:1000 
                  RX bytes:2151990 (2.0 MiB)  TX bytes:1768340 (1.6 MiB)
        ...
        
"""


from Products.ZenRRD.ComponentCommandParser import ComponentCommandParser

class ifconfig(ComponentCommandParser):

    componentSplit = '\n\n'

    componentScanner = '^(?P<component>.*):?[ \t]+Link '

    scanners = [
        r' RX packets:(?P<ifInPackets>\d+) errors:(?P<ifInErrors>\d+)',
        r' TX packets:(?P<ifOutPackets>\d+) errors:(?P<ifOutErrors>\d+)',
        r' RX bytes:(?P<ifInOctets>\d+) ',
        r' TX bytes:(?P<ifOutOctets>\d+) ',
        ]

    componentScanValue = 'interfaceName'
