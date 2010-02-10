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
from Products.ZenUtils.Utils import prepId
from Products.Zuul.interfaces import ICatalogTool
from Products.Zuul.interfaces import ITemplateNode
from Products.Zuul.interfaces import ITemplateLeaf
from Products.Zuul.interfaces import IDataSourceInfo
from Products.Zuul.interfaces import IDataPointInfo
from Products.Zuul.interfaces import IThresholdInfo
from Products.Zuul.interfaces import IGraphInfo
from Products.Zuul.utils import unbrain
from Products.Zuul.facades import ZuulFacade
from Products.ZenModel.RRDTemplate import RRDTemplate
from Products.ZenModel.RRDDataSource import RRDDataSource
from Products.ZenModel.RRDDataPoint import RRDDataPoint
from Products.ZenModel.ThresholdClass import ThresholdClass
from Products.ZenModel.GraphDefinition import GraphDefinition

log = logging.getLogger('zen.TemplateFacade')

class TemplateFacade(ZuulFacade):

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

    def deleteTemplate(self, uid):
        obj = self._getObject(uid)
        context = aq_parent(obj)
        context._delObject(obj.id)

    def getDataSources(self, uid):
        catalog = self._getCatalog(uid)
        if isinstance(catalog.context, RRDTemplate):
            brains = catalog.search(types=RRDDataSource)
            dataSources = imap(unbrain, brains)
            infos = imap(IDataSourceInfo, dataSources)
        else:
            brains = catalog.search(types=RRDDataPoint)
            dataPoints = imap(unbrain, brains)
            infos = imap(IDataPointInfo, dataPoints)
        return infos

    def getThresholds(self, uid):
        catalog = self._getCatalog(uid)
        brains = catalog.search(types=ThresholdClass)
        thresholds = imap(unbrain, brains)
        return imap(IThresholdInfo, thresholds)

    def getThresholdTypes(self):
        data = []
        template = self._dmd.Devices.rrdTemplates.Device
        for pythonClass, type in template.getThresholdClasses():
            data.append({'type': type})
        return data

    def addThreshold(self, uid, thresholdType, thresholdId, dataPoints):
        thresholdId = prepId(thresholdId)
        template = self._getObject(uid)
        thresholds = template.thresholds
        for pythonClass, key in template.getThresholdClasses():
            if key == thresholdType:
                thresholds._setObject(thresholdId, pythonClass(thresholdId))
                break
        else:
            raise Exception('Unknow threshold type: %s' % thresholdType)
        threshold = getattr(thresholds, thresholdId)
        def dsnames():
            for dataPointUid in dataPoints:
                dataPoint = self._getObject(dataPointUid)
                yield dataPoint.name()
        threshold.dsnames.extend(dsnames())

    def getGraphs(self, uid):
        catalog = self._getCatalog(uid)
        brains = catalog.search(types=GraphDefinition)
        graphs = imap(unbrain, brains)
        return imap(IGraphInfo, graphs)

    def _getCatalog(self, uid):
        obj = self._getObject(uid)
        return ICatalogTool(obj)
        
    def _getObject(self, uid):
        try:
            obj = self._dmd.unrestrictedTraverse(uid)
        except Exception, e:
            args = (uid, e.__class__.__name__, e)
            raise Exception('Cannot find "%s". %s: %s' % args)
        return obj
