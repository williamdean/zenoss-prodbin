###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2010, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

import logging
from itertools import imap
from Acquisition import aq_parent
from zope.interface import implements
from Products.ZenUtils.Utils import prepId
from Products import Zuul
from Products.Zuul.interfaces import ITemplateFacade, ICatalogTool, ITemplateNode, IRRDDataSourceInfo, \
    IDataPointInfo, IThresholdInfo, IGraphInfo, IInfo, ITemplateLeaf, IGraphPointInfo
from Products.Zuul.infos.template import SNMPDataSourceInfo, CommandDataSourceInfo
from Products.Zuul.utils import unbrain, safe_hasattr as hasattr
from Products.Zuul.facades import ZuulFacade
from Products.ZenModel.RRDTemplate import RRDTemplate
from Products.ZenModel.RRDDataSource import RRDDataSource
from Products.ZenModel.BasicDataSource import BasicDataSource
from Products.ZenModel.RRDDataPoint import RRDDataPoint
from Products.ZenModel.ThresholdClass import ThresholdClass
from Products.ZenModel.GraphDefinition import GraphDefinition
from Products.ZenModel.GraphPoint import GraphPoint
from Products.ZenModel.Device import Device
from Products.ZenModel.DeviceClass import DeviceClass

log = logging.getLogger('zen.TemplateFacade')

class TemplateFacade(ZuulFacade):
    implements(ITemplateFacade)

    def getTemplates(self):
        catalog = self._getCatalog('/zport/dmd/Devices')
        brains = catalog.search(types=RRDTemplate)
        templates = imap(unbrain, brains)
        nodes = {}
        for template in templates:
            if template.id not in nodes:
                nodes[template.id] = ITemplateNode(template)
            leaf = ITemplateLeaf(template)
            nodes[template.id]._addChild(leaf)
        for key in sorted(nodes.keys(), key=str.lower):
            yield nodes[key]        

    def addTemplate(self, id):
        id = prepId(id)
        relationship = self._dmd.Devices.rrdTemplates
        relationship._setObject(id, RRDTemplate(id))
        template = getattr(relationship, id)
        node = ITemplateNode(template)
        leaf = ITemplateLeaf(template)
        node._addChild(leaf)
        return node
    
    def _deleteObject(self, uid):
        """
        Deletes the object by getting the parent
        and then calling delete on the objects id.
        @param string uid Must be a valid path
        """
        obj = self._getObject(uid)
        context = aq_parent(obj)
        context._delObject(obj.id)
        
    def deleteTemplate(self, uid):
        return self._deleteObject(uid)

    def _editDetails(self, info, data):
        """
        Will apply every property in data to the info if
        it has that attribute
        @param IInfoBase (or descendant)
        @param Dictionary of the form {propertyName: propertyValue}
        @return IInfoBase with the properties changed
        """
        for key in data.keys():
            if hasattr(info, key):
                setattr(info, key, data[key])
        return info
    
    def getDataSources(self, uid):
        catalog = self._getCatalog(uid)
        if isinstance(catalog.context, RRDTemplate):
            brains = catalog.search(types=RRDDataSource)
            dataSources = imap(unbrain, brains)
            infos = imap(IRRDDataSourceInfo, dataSources)
        else:
            brains = catalog.search(types=RRDDataPoint)
            dataPoints = imap(unbrain, brains)
            infos = imap(IDataPointInfo, dataPoints)
        return infos

    def _getDataSourceInfoFromObject(self, obj):
        """
        Given the obj this returns the correct info. We can not rely on
        adapt for datasources since we need different info objects depending on
        their type not the subclass.

        This defaults to using the adapters to return the correct info if not a datasource.
        """
        info = None
        
        # look for datasource type
        if isinstance(obj, BasicDataSource):
            if obj.sourcetype == 'SNMP':
                info = SNMPDataSourceInfo(obj)
            if obj.sourcetype == 'COMMAND':
                info = CommandDataSourceInfo(obj)
                
        # use the default adapter    
        if not info:
            info = IInfo(obj)
        
        return info
    
    def getDataSourceDetails(self, uid):
        """
        Given the unique id of the datasource we will
        return an IDataSourceInfo (or subclass) that has the properties populated
        @param string uid absolute id of the datasource
        @returns IDataSourceInfo
        """
        obj = self._getObject(uid)
        return self._getDataSourceInfoFromObject(obj)
        
    def setInfo(self, uid, data):
        """
        Given a dictionary of {property name: property value}
        this will populate the datapoint
        @param string uid unique identifier of the object we are editing
        @param Dictionary of properties to update
        @return IInfo with the updated properties
        """
        obj = self._getObject(uid)
        info = self._getDataSourceInfoFromObject(obj)
        return self._editDetails(info, data)
    
    def getDataPointDetails(self, uid):
        """
        @param string unique Identifier of a datapoint
        @returns IDataPointInfo 
        """
        obj = self._getObject(uid)
        return IDataPointInfo(obj)
    
    def getThresholds(self, uid):
        catalog = self._getCatalog(uid)
        brains = catalog.search(types=ThresholdClass)
        thresholds = imap(unbrain, brains)
        return imap(IThresholdInfo, thresholds)
    
    def getThresholdDetails(self, uid):
        """
        @param String uid: the id of the threshold
        @returns IThresholdInfo 
        """
        threshold = self._getObject(uid)
        template = threshold.rrdTemplate()
        info = IThresholdInfo(threshold)
        # don't show the "selected one" in the list of avaialble
        info.allDataPoints = [point for point in template.getRRDDataPointNames() if not point in info.dataPoints]
        return info

    def addDataPoint(self, dataSourceUid, name):
        """
        Adds a datapoint to the datasource specified by the UID
        @param string dataSourceUid unique identifier of a datasource
        @parma string name 
        """
        datasource = self._getObject(dataSourceUid)
        return datasource.manage_addRRDDataPoint(str(name))
    
    def addDataSource(self, templateUid, name, type):
        """
        Adds a datasource to a template
        @param string templateUid unique identifier of the template
        @param string name name of our datasource
        @param string type must be a valid datasource type (see RRDTemplate getDataSourceOptions)
        """
        template = self._getObject(templateUid)
        
        # get our option information based on the string type inputed
        selectedOption = None
        options = template.getDataSourceOptions() # comes back in a (name, typeinformation) tuple
        for option in options:
            if option[0] == type:
                selectedOption = option[1]
                
        if selectedOption is None:
            raise "%s is not a valid DataSource Type" % type
        
        # create the datasource and return it
        datasource = template.manage_addRRDDataSource(name, selectedOption)
        return datasource
    
    def getDataSourceTypes(self):
        """
        @returns [] List of all of the datasource types (in string form)
        """
        data = []
        template = self._dmd.Devices.rrdTemplates.Device
        for name, dsOption in template.getDataSourceOptions():
            data.append({'type': name})
        return data
    
    def getThresholdTypes(self):
        data = []
        template = self._dmd.Devices.rrdTemplates.Device
        for pythonClass, type in template.getThresholdClasses():
            data.append({'type': type})
        return data

    def addThreshold(self, uid, thresholdType, thresholdId, dataPoints=None):
        
        thresholdId = prepId(thresholdId)
        template = self._getObject(uid)
        thresholds = template.thresholds
        for pythonClass, key in template.getThresholdClasses():
            if key == thresholdType:
                thresholds._setObject(thresholdId, pythonClass(thresholdId))
                break
        else:
            raise Exception('Unknown threshold type: %s' % thresholdType)
        threshold = getattr(thresholds, thresholdId)
        dsnames = self._translateDataPoints(dataPoints)
        threshold._updateProperty('dsnames', dsnames)

    def _translateDataPoints(self, dataPoints):
        """ Takes the list of datapoints from te server
        and turns them into the proper dsnames that the
        threshold items expects
        @param List dataPointsUids
        @return List proper names from the dataPoint object
        """
        dsnames = []
        for dataPointUid in dataPoints:
            dataPoint = self._getObject(dataPointUid)
            dsnames.append( dataPoint.name() )
        return dsnames
            
    def removeThreshold(self, uid):
        """Removes the threshold
        @param string uid
        """
        return self._deleteObject(uid)
    
    def getGraphs(self, uid):
        catalog = self._getCatalog(uid)
        brains = catalog.search(types=GraphDefinition)
        graphs = map(IGraphInfo, imap(unbrain, brains))
        graphs.sort(key=lambda graph: graph.sequence)
        return graphs.__iter__()

    def addDataPointToGraph(self, dataPointUid, graphUid):
        dataPoint = self._getObject(dataPointUid)
        graph = self._getObject(graphUid)
        graph.manage_addDataPointGraphPoints([dataPoint.name()])

    def getCopyTargets(self, uid, query=''):
        template = self._getTemplate(uid)
        catalog = ICatalogTool(self._dmd)
        types = ['Products.ZenModel.DeviceClass.DeviceClass',
                 'Products.ZenModel.Device.Device']
        brains = catalog.search(types=types)
        objs = imap(unbrain, brains)
        def genTargets():
            for obj in objs:
                if isinstance(obj, Device):
                    container = obj
                    last = -2
                else:
                    container = obj.rrdTemplates
                    last = -1
                if template.id not in container.objectIds():
                    organizer = '/' + '/'.join(obj.getPrimaryPath()[3:last])
                    label = '%s in %s' % (obj.titleOrId(), organizer)
                    if label.lower().startswith(query.lower()):
                        uid = '/'.join(obj.getPrimaryPath())
                        yield dict(uid=uid, label=label)
        def byLabel(left, right):
            return cmp(left['label'].lower(), right['label'].lower())
        return sorted(genTargets(), byLabel)
        
    def copyTemplate(self, uid, targetUid):
        template = self._getTemplate(uid)
        target = self._getObject(targetUid)
        marker = object()
        source = getattr(template, 'device', marker)
        if source is marker and isinstance(target, DeviceClass):
            # copying to and from a DeviceClass
            source = template.deviceClass()
            source.manage_copyAndPasteRRDTemplates((template.id,), targetUid)
        else:
            if isinstance(target, DeviceClass):
                # copying from a Device to a DeviceClass
                container = target.rrdTemplates
            else:
                # copying from either to a Device
                container = target
            if template.id in container.objectIds():
                msg = '"%s" already contains template "%s".'
                args = (targetUid, template.id)
                raise Exception(msg % args)
            copy = template._getCopy(container)
            container._setObject(copy.id, copy)

    def addGraphDefinition(self, templateUid, graphDefinitionId):
        template = self._getTemplate(templateUid)
        template.manage_addGraphDefinition(graphDefinitionId)

    def deleteGraphDefinition(self, uid):
        graphDefinition = self._getObject(uid)
        template = graphDefinition.rrdTemplate()
        template.manage_deleteGraphDefinitions((graphDefinition.id,))

    def deleteGraphPoint(self, uid):
        """
        Deletes a graph point
        """
        graphPoint = self._getObject(uid)
        graphDef = graphPoint.graphDef()
        graphDef.manage_deleteGraphPoints((graphPoint.id,))

    def getGraphPoints(self, uid):
        graphDefinition = self._getObject(uid)
        graphPoints = graphDefinition.getGraphPoints()
        for graphPoint in graphPoints:
            yield IGraphPointInfo(graphPoint)

    def getInfo(self, uid):
        """
        @param uid unique identifier of an object
        @returns the info object as identified by the UID
        """
        obj = self._getObject(uid)
        return IInfo(obj)
        
    def addThresholdToGraph(self, graphUid, thresholdUid):
        graphDefinition = self._getObject(graphUid)
        thresholdClass = self._getThresholdClass(thresholdUid)
        graphDefinition.manage_addThresholdGraphPoints((thresholdClass.id,))

    def addCustomToGraph(self, graphUid, customId, customType):
        graphDefinition = self._getObject(graphUid)
        graphDefinition.manage_addCustomGraphPoint(customId, customType)

    _graphInstructionTypes = (('DefGraphPoint', 'DEF'),
                              ('VdefGraphPoint', 'VDEF'),
                              ('CdefGraphPoint', 'CDEF'),
                              ('PrintGraphPoint', 'PRINT'),
                              ('GprintGraphPoint', 'GPRINT'),
                              ('CommentGraphPoint', 'COMMENT'),
                              ('VruleGraphPoint', 'VRULE'),
                              ('HruleGraphPoint', 'HRULE'),
                              ('LineGraphPoint', 'LINE'),
                              ('AreaGraphPoint', 'AREA'),
                              ('TickGraphPoint', 'TICK'),
                              ('ShiftGraphPoint', 'SHIFT'))

    def getGraphInstructionTypes(self):
        for pythonClassName, label in self._graphInstructionTypes:
            yield dict(pythonClassName=pythonClassName, label=label)

    def setGraphPointSequence(self, uids):
        for i, uid in enumerate(uids):
            graphPoint = self._getGraphPoint(uid)
            graphPoint.sequence = i

    def getGraphDefinition(self, uid):
        obj = self._getObject(uid)
        if not isinstance(obj, GraphDefinition):
            raise Exception('Cannot find GraphDefinition at "%s".' % uid)
        return IInfo(obj)
        
    def setGraphDefinition(self, uid, data):
        graphDef = self._getObject(uid)
        Zuul.unmarshal(data, graphDef)

        
    def _setGraphDefinitionSequence(self, uids):
        for i, uid in enumerate(uids):
            graphDefinition = self.getGraphDefinition(uid)
            graphDefinition.sequence = i

    def _getCatalog(self, uid):
        obj = self._getObject(uid)
        return ICatalogTool(obj)

    def _getTemplate(self, uid):
        obj = self._getObject(uid)
        if not isinstance(obj, RRDTemplate):
            raise Exception('Cannot find RRDTemplate at "%s".' % uid)
        return obj

    def _getThresholdClass(self, uid):
        obj = self._getObject(uid)
        if not isinstance(obj, ThresholdClass):
            raise Exception('Cannot find ThresholdClass at "%s".' % uid)
        return obj

    def _getGraphPoint(self, uid):
        obj = self._getObject(uid)
        if not isinstance(obj, GraphPoint):
            raise Exception('Cannot find GraphPoint at "%s".' % uid)
        return obj
