/*****************************************************************************
 *
 * Copyright (C) Zenoss, Inc. 2013, all rights reserved.
 *
 * This content is made available according to terms specified in
 * License.zenoss under the directory where your Zenoss product is installed.
 *
 ****************************************************************************/
(function(){
    Ext.ns('Daemons');

    Daemons.menuItems = Daemons.menuItems || [];

    /**
     * @class Daemons.view.daemons.SearchField
     * @extends Ext.form.TextField
     * @constructor
     */
    Ext.define("Daemons.view.daemons.SearchField", {
        extend: "Ext.form.TextField",
        alias: ['widget.daemonsearchfield'],
        constructor: function(config){
            config = Ext.applyIf(config||{}, {
                validationDelay: 500,
                selectOnFocus: true
            });
            config.cls += ' x-field-search';
            this.callParent([config]);
        },
        getClass: function(){
            var cls = this.altCls ? this.altCls : 'searchfield';
            return this.black ? cls + '-black' : cls;
        }
    });

    /**
     * @class Daemons.view.daemons.List
     * @extends Ext.tree.Panel
     * @constructor
     * This class represents the TreeGrid of all the deamons and services.
     */
    Ext.define('Daemons.view.daemons.List' ,{
        extend: 'Ext.tree.Panel',
        alias: 'widget.daemonslist',
        title: _t('All Daemons'),
        stores: ['Daemons'],
        multiSelect: true,
        rootVisible: true,
        useArrows: true,
        animate: false,
        rootVisible: false,
        viewConfig: {
            plugins: {
                ptype:'treeviewdragdrop',
                dropGroup: 'assignCollector'
            }
        },
        dockedItems: [{
            xtype: 'toolbar',
            dock: 'top',
            items: Daemons.menuItems.concat([{
                xtype: 'button',
                iconCls: 'customize',
                menu: [{
                    text: _t('View Performance Templates'),
                    handler: function() {
                        // redirect to the collector template page
                        window.location = "/zport/dmd/collectorTemplate";
                    }
                }]

            },'-', {
                xtype: 'button',
                text: _t('Start'),
                ref: 'start'
            },{
                xtype: 'button',
                text: _t('Stop'),
                ref: 'stop'
            },{
                xtype: 'button',
                text: _t('Restart'),
                ref: 'restart'
            },'->',{
                xtype: 'daemonsearchfield',
                id: 'component_searchfield',
                emptyText: _t('Type to filter...'),
                enableKeyEvents: true
            },{
                xtype: 'refreshmenu',
                stateId: 'devicerefresh',
                iconCls: 'refresh',
                ref: "refresh",
                id: 'refreshtreegrid',
                text: _t('Refresh')
            }])
        }],
        selectionModel: 'rowmodel',
        initComponent: function() {
            this.columns = [{
                xtype: 'treecolumn', //this is so we know which column will show the tree
                text: _t('Name'),
                flex: 2,
                sortable: true,
                dataIndex: 'name'
            },{
                text: _t('Type'),
                flex: .15,
                tooltip: _t('Type'),
                dataIndex: 'type',
                sortable: true
            },{
                text: _t('Uptime'),
                flex: .25,
                tooltip: _t('Uptime'),
                dataIndex: 'uptime',
                sortable: true
            }, {
                text: _t('Logs'),
                flex: .25,
                tooltip: _t('Deamon logs'),
                dataIndex: 'id',
                sortable: true,
                renderer: function(value, m, record) {
                    if (record.isDaemon()) {
                        return Ext.String.format("<a target='_blank' href='/zport/dmd/getDaemonLogs?id={0}'>{1}</a>",
                                                 value,
                                                 _t('View Logs'));
                    }
                    return "";
                }
            },{
                xtype: 'actioncolumn',
                text: _t('AutoStart'),
                flex: .25,
                dataIndex: 'autostart',
                tooltip: _t('Automatically or manually start this deamon'),
                ref: 'autostart',
                sortable: true,
                getClass: function(v, m, record) {
                    if (!record.isDaemon()) {
                        return "";
                    }
                    if (record.data.autostart) {
                        return 'grid-action checked enabled';
                    } else {
                        return 'grid-action unchecked enabled';
                    }
                }
            },{
                text: _t('Restart'),
                flex: .1,
                menuDisabled: true,
                xtype: 'actioncolumn',
                tooltip: _t('restart deamon'),
                refreshingIcon: '/++resource++zenui/img/ext4/icon/circle_arrows_ani.gif',
                stillIcon: '/++resource++zenui/img/ext4/icon/circle_arrows_still.png',
                ref: 'restartcolumn',
                items: [{
                    icon: '/++resource++zenui/img/ext4/icon/circle_arrows_still.png',
                    iconCls: 'restarticon'
                }],
                renderer: function(value, meta, record) {
                    if (record.isDaemon()) {
                        return '<img class="x-action-col-icon x-action-col-0 restarticon" src="/++resource++zenui/img/ext4/icon/circle_arrows_still.png" alt="">';
                    }
                    return "";
                },
                /**
                 * Action columns expect an image so override the
                 * defaultRenderer to just use the supplied renderer
                 **/
                defaultRenderer: function(v, meta, record, rowIdx, colIdx, store, view) {
                    return this.origRenderer.apply(this, arguments);
                }
            },{
                text: _t('State'),
                flex: .25,
                xtype: 'actioncolumn',
                ref: 'statuscolumn',
                tooltip: _t('Click to stop/start the deamon'),
                dataIndex: 'state',
                sortable: true,
                renderer: function(value) {
                    if (value == 'up' || value == 'down'){
                        return Zenoss.render.pingStatus(value);
                    }
                    return value + "...";
                },
                /**
                 * Action columns expect an image so override the
                 * defaultRenderer to just use the supplied renderer (pingStatus)
                 **/
                defaultRenderer: function(v, meta, record, rowIdx, colIdx, store, view) {
                    return this.origRenderer.apply(this, arguments);
                }
            }];

            this.callParent(arguments);
        }
    });

})();