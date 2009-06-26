###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2009, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################
import Migrate
from zExceptions import NotFound
import logging

log = logging.getLogger("zen.migrate")

class UseIntLoadAverages(Migrate.Step):
    """
    The laLoadInt1 and laLoadInt15 data point were added to the standard
    Linux and Solaris Device templates in 2.3.0. However, they were added using
    the STRING version of the OID instead of the INTEGER version. This caused
    a scaling error, and was corrected in the stock objects.xml in 2.4.0.

    This migrate script is needed to fix the OIDs in an upgrade. Fresh installs
    already work properly.

    http://dev.zenoss.org/trac/ticket/3979#comment:15
    """

    version = Migrate.Version(2, 4, 2)

    def cutover(self, dmd):
        dsPaths = (
            'Server/Linux/rrdTemplates/Device/datasources/laLoadInt1',
            'Server/Linux/rrdTemplates/Device/datasources/laLoadInt15',
            'Server/Solaris/rrdTemplates/Device/datasources/laLoadInt1',
            'Server/Solaris/rrdTemplates/Device/datasources/laLoadInt15',
            )

        for dsPath in dsPaths:
            try:
                ds = dmd.getObjByPath('/zport/dmd/Devices/' + dsPath)
                if ds.oid.startswith('1.3.6.1.4.1.2021.10.1.3'):
                    ds.oid = ds.oid.replace(
                        '1.3.6.1.4.1.2021.10.1.3',
                        '1.3.6.1.4.1.2021.10.1.5')

            except AttributeError, KeyError:
                pass
            except NotFound:
                log.info( ( 'Could not retrieve datasource at %s. ' +
                            'The template or datasource is not present.' ),
                            dsPath )


useIntLoadAverages = UseIntLoadAverages()
