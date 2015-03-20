Ext.onReady(function(){
    /**
     * Settings panel
     **/
    Ext.define('Zenoss.NetworkMapSettings', {
        extend: 'Ext.panel.Panel',
        alias: 'widget.networkmapsettings',
        initComponent: function() {
            Ext.applyIf(this, {
                padding: 10,
                items: [{
                    xtype: 'form',
                    layout: 'hbox',
                    defaults: {
                        labelAlign: 'top',
                        marginLeft: 10
                    },
                    items: [ {
                        xtype: 'combo',
                        name: 'network',
                        queryMode: 'local',
                        fieldLabel: _t('Network'),
                        editable: false,
                        displayField: 'name',
                        valueField: 'uid',
                        store: new Zenoss.NonPaginatedStore({
                            directFn: Zenoss.remote.NetworkRouter.getNetworks,
                            root: 'data',
                            autoLoad: true,
                            fields: ['uid', 'name']
                        })}]
                },{
                    xtype: 'button',
                    text: _t('Refresh')
                },{
                    xtype: 'container',
                    html: '<hr />'
                }]
            });
            this.callParent(arguments);
        }
    });

    /**
     * Network Map
     **/
    Ext.define('Zenoss.NetworkMap', {
        extend: 'Ext.panel.Panel',
        alias: 'widget.networkmap',
        network: null,
        filter: "/",
        depth: 3,
        initComponent: function(){
            this.networkMapId = Ext.id();
            Ext.apply(this, {
                items: [{
                    xtype: 'container',
                    id: this.networkMapId
                }],
                height: this.height
            });

            this.callParent(arguments);
            this.on('afterrender', this.buildNetworkMap, this, {single: true});
        },
        destroyOldMap: function() {
            var el = Ext.get(this.networkMapId);
            // destroy all the children and build the map
            while (el.dom.firstChild) {
                el.dom.removeChild(el.dom.firstChild);
            }
        },
        resizeSVG: function(panel, width, height) {
            var el = Ext.get(this.networkMapId);
            Ext.get(this.networkMapId).setHeight(height -10);
            Ext.get(this.networkMapId).setWidth(width -10);
            this.svg.attr("height", height);
            this.svg.attr("width", width);
        },
        buildNetworkMap: function() {
            // make sure we have a network first
            if (!this.network) {
                return;
            }
            this.destroyOldMap();
            // resize the svg whenever we are resized
            this.on('resize', this.resizeSVG, this);
            var el = Ext.get(this.networkMapId);
            var self = this, attachPoint = d3.select("#" +this.networkMapId);
            self.imageDir="/zport/dmd/img/icons";
            var width = Math.max(attachPoint.style('width').replace("px", ""), 600);
            var height = Math.max(attachPoint.style('height').replace("px", ""), 400);

            self.attachPoint = attachPoint;


            this.nodes = [];
            this.links = [];
            this.force = d3.layout.force()
                .charge(-1000)
                .theta(0)
                .linkDistance(225)
                .size([width, height])
                .nodes(this.nodes)
                .links(this.links)
                .on("tick", Ext.bind(this.tick, this));
            //this.force.drag().on("dragstart", function(d) { d.fixed = true;});
            this.svg = this.attachPoint.append("svg")
                .attr("width", width)
                .attr("height", height);

            self.update();
        },
        tick: function() {
            var node = this.svg.selectAll(".node");
            var link = this.svg.selectAll(".link");
            link.attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node.attr("transform", function(d) { return "translate(" + d.x + ", " + d.y + ")"; });
        },
        update: function() {
            var self = this,
                node = this.svg.selectAll(".node"),
                link = this.svg.selectAll(".link"),
                nodeHeight = 40,
                nodeWidth = 125;
            Zenoss.remote.NetworkRouter.getNetworkMapData({
                uid: self.network,
                filter: self.filter,
                depth: self.depth
            }, function(response) {
                if (!response.success) {
                    return;
                }
                var graph = response.data;
                graph.nodes.forEach(function(n){
                    self.nodes.push(n);
                });

                node = node.data(self.force.nodes(), function(d) { return d.id; });
                var nodeContainer = node.enter()
                    .append("g")
                    .attr("class", function(d){ return "node " + d.id; })
                    .call(self.force.drag);
                nodeContainer.append("rect")
                    .attr("width", function(d) {
                        // make the box wider for longer names
                        return Math.max(d.id.length * 8, 125);
                    })
                    .attr("height", nodeHeight)
                    .attr("transform", "translate(" + -nodeWidth/2 + ", " + -nodeHeight/2 + ")")
                    .attr("rx", 10)
                    .attr("ry", 10)
                    .attr("stroke", function(d){ return d.color; });

                nodeContainer.append("text")
                    .text(function(d){ return d.id; })
                    .attr("dx", -30)
                    .attr("dy", 5);
                nodeContainer.append("svg:image")
                    .attr("xlink:href", function(d){ return self.imageDir + "/" + d.icon; })
                    .attr("height", 30)
                    .attr("width", 30)
                    .attr("x", -nodeWidth/2)
                    .attr("y", -15);
                node.exit().remove();

                graph.links.forEach(function(e){
                    var sourceNode = graph.nodes.filter(function(n) { return n.id === e.source; });
                    var targetNode = graph.nodes.filter(function(n) { return n.id === e.target; });
                    self.links.push({source: sourceNode[0], target: targetNode[0]});
                });

                link = link.data(self.force.links(), function(d) { return d.source.id + "-" + d.target.id; });
                link.enter().insert("line", ".node")
                    .attr("class", "link");
                link.exit().remove();

                self.force.start();
            }, this);
        },
        setContext: function(uid) {
            this.network = uid;
            if (this.svg) {
                this.buildNetworkMap();
            }
        }
    });

    /**
     * Add to center_panel
     *
     **/
    var center_panel = Ext.getCmp('center_panel');
    center_panel.add({
        xtype: 'networkmap',
        network: '/zport/dmd/Devices/CiscoUCS/UCS-Manager/devices/ucs1',
        dockedItems: [{
            xtype: 'networkmapsettings',
            dock: 'top'
        }]
    });

    /**
     * Controller setup
     **/
    // when you select a network from the drop down
    center_panel.down("combo[name='network']").on('select', function(combo, selected) {
        if (!selected.length) {
            return;
        }
        var value = selected[0];
        center_panel.down('networkmap').setContext(value.get('uid'));
    });

    // when you press the refresh button
    center_panel.down('button').on('click', function(){
        center_panel.down('networkmap').buildNetworkMap();
    });
});
