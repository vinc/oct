# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Vincent Ollivier <contact@vincentollivier.com>

This file is part of OpenNMS Configuration Tools.

OpenNMS Configuration Tools is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Foobar is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenNMS Configuration Tools. If not, see <http://www.gnu.org/licenses/>.
"""

from plugin import Plugin

# Allways run 'config.py --remove' before doing any modifications to this
# file to clean remove the old plugin before installing the new version with
# 'config.py --save'.

class Nginx(Plugin):
    def __init__(self, path):
        super(Nginx, self).__init__(path)

        # List all modifications done to the configuration for this plugin.
        # 'self._list_xml_modifications' is a dict where each key is the name of
        # a node to add to a XML configuration file. The name of this file is
        # the value associated to the key.
        #
        # {nodename1: filename1, nodename2: filename2}
        self._list_xml_modifications = {
            "protocol-plugin": "capsd-configuration.xml",
            "service": "collectd-configuration.xml",
            "collector": "collectd-configuration.xml",
            "http-collection": "http-datacollection-config.xml",
        }

        # Add a node 'protocol-plugin' to the file 'capsd-configuration.xml'
        self._xml_protocol_plugin = """
        <protocol-plugin protocol="Nginx-Stats"
            class-name="org.opennms.netmgt.capsd.plugins.HttpPlugin" scan="on"
            user-defined="false">
            <property key="port" value="80" />
            <property key="timeout" value="3000" />
            <property key="retry" value="2" />
            <property key="url" value="/nginx_status" />
        </protocol-plugin>
        """

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_service = """
        <service name="Nginx-Stats" interval="300000" user-defined="false"
            status="on" >
            <parameter key="http-collection" value="nginx-stats" />
            <parameter key="retry" value="1" />
            <parameter key="timeout" value="2000" />
        </service>
        """

        # Add a node 'collector' to the file 'collectd-configuration.xml'
        self._xml_collector = """
        <collector service="Nginx-Stats"
            class-name="org.opennms.netmgt.collectd.HttpCollector" />
        """

        # Add a node 'http-collection' to the file 'http-datacollection-config.xml'
        # Python requierement: '-' is replaced by '_' in the variable name
        self._xml_http_collection = """
        <http-collection name="Nginx-Stats">
            <rrd step="300">
                <rra>RRA:AVERAGE:0.5:1:8928</rra>
                <rra>RRA:AVERAGE:0.5:12:8784</rra>
                <rra>RRA:MIN:0.5:12:8784</rra>
                <rra>RRA:MAX:0.5:12:8784</rra>
            </rrd>
            <uris>
                <uri name="nginx">
                    <url path="/nginx_status"
                        user-agent="OpenNMS HTTP Datacollection"
                        matches="(?s).*?Active\sconnections:\s([0-9]+).*?([0-9]+)\s([0-9]+)\s([0-9]+).*?Reading:\s([0-9]+)\sWriting:\s([0-9]+)\sWaiting:\s([0-9]+).*" response-range="100-399" >
                    </url>
                    <attributes>
                        <attrib alias="nginxActive" match-group="1" type="gauge32" />
                        <attrib alias="nginxAccepts" match-group="2" type="counter32" />
                        <attrib alias="nginxHandled" match-group="3" type="counter32" />
                        <attrib alias="nginxRequests" match-group="4" type="counter32" />
                        <attrib alias="nginxReading" match-group="5" type="gauge32" />
                        <attrib alias="nginxWriting" match-group="6" type="gauge32" />
                        <attrib alias="nginxWaiting" match-group="7" type="gauge32" />
                    </attributes>
                </uri>
            </uris>
        </http-collection>
        """

        # Define a list of report graph we'll add to the configuration
        self._report_defs = ["nginx.server.connections", "nginx.server.stats", "nginx.server.active"]

        # Define all the report graph
        # Python requierement: 'r' is needed before the string definition to
        # ensure the use of raw string to keep the return line.
        self._report_graph = r"""
        report.nginx.server.connections.name=NGINX Connections
        report.nginx.server.connections.columns=nginxReading, nginxWriting, nginxWaiting
        report.nginx.server.connections.type=nodeSnmp
        report.nginx.server.connections.command=--title="NGINX Connections" \
         --vertical-label="count" \
         --lower-limit 0 \
         DEF:avgReading={rrd1}:nginxReading:AVERAGE \
         DEF:minReading={rrd1}:nginxReading:MIN \
         DEF:maxReading={rrd1}:nginxReading:MAX \
         DEF:avgWriting={rrd2}:nginxWriting:AVERAGE \
         DEF:minWriting={rrd2}:nginxWriting:MIN \
         DEF:maxWriting={rrd2}:nginxWriting:MAX \
         DEF:avgWaiting={rrd3}:nginxWaiting:AVERAGE \
         DEF:minWaiting={rrd3}:nginxWaiting:MIN \
         DEF:maxWaiting={rrd3}:nginxWaiting:MAX \
         AREA:avgReading#0000ff:"Reading" \
         GPRINT:avgReading:AVERAGE:"Avg \\: %10.2lf %s" \
         GPRINT:minReading:MIN:"Min \\: %10.2lf %s" \
         GPRINT:maxReading:MAX:"Max \\: %10.2lf %s\n" \
         STACK:avgWriting#ff0000:"Writing" \
         GPRINT:avgWriting:AVERAGE:"Avg \\: %10.2lf %s" \
         GPRINT:minWriting:MIN:"Min \\: %10.2lf %s" \
         GPRINT:maxWriting:MAX:"Max \\: %10.2lf %s\n" \
         STACK:avgWaiting#ffba00:"Waiting" \
         GPRINT:avgWaiting:AVERAGE:"Avg \\: %10.2lf %s" \
         GPRINT:minWaiting:MIN:"Min \\: %10.2lf %s" \
         GPRINT:maxWaiting:MAX:"Max \\: %10.2lf %s\\n"

        report.nginx.server.stats.name=NGINX Statistics
        report.nginx.server.stats.columns=nginxAccepts, nginxHandled, nginxRequests
        report.nginx.server.stats.type=nodeSnmp
        report.nginx.server.stats.command=--title="NGINX Statistics" \
         --vertical-label="count" \
         --lower-limit 0 \
         DEF:avgAccept={rrd1}:nginxAccepts:AVERAGE \
         DEF:minAccept={rrd1}:nginxAccepts:MIN \
         DEF:maxAccept={rrd1}:nginxAccepts:MAX \
         DEF:avgHandled={rrd2}:nginxHandled:AVERAGE \
         DEF:minHandled={rrd2}:nginxHandled:MIN \
         DEF:maxHandled={rrd2}:nginxHandled:MAX \
         DEF:avgRequests={rrd3}:nginxRequests:AVERAGE \
         DEF:minRequests={rrd3}:nginxRequests:MIN \
         DEF:maxRequests={rrd3}:nginxRequests:MAX \
         AREA:avgAccept#0000ff:"Accept" \
         GPRINT:avgAccept:AVERAGE:"  Avg \\: %10.2lf %s" \
         GPRINT:minAccept:MIN:"Min \\: %10.2lf %s" \
         GPRINT:maxAccept:MAX:"Max \\: %10.2lf %s\n" \
         STACK:avgHandled#ff0000:"Handled" \
         GPRINT:avgHandled:AVERAGE:" Avg \\: %10.2lf %s" \
         GPRINT:minHandled:MIN:"Min \\: %10.2lf %s" \
         GPRINT:maxHandled:MAX:"Max \\: %10.2lf %s\n" \
         STACK:avgRequests#ffba00:"Requests" \
         GPRINT:avgRequests:AVERAGE:"Avg \\: %10.2lf %s" \
         GPRINT:minRequests:MIN:"Min \\: %10.2lf %s" \
         GPRINT:maxRequests:MAX:"Max \\: %10.2lf %s\\n"

        report.nginx.server.active.name=NGINX Active Connections
        report.nginx.server.active.columns=nginxActive
        report.nginx.server.active.type=nodeSnmp
        report.nginx.server.active.command=--title="NGINX active connections" \
         --vertical-label="count" \
         --lower-limit 0 \
         DEF:avgActive={rrd1}:nginxActive:AVERAGE \
         DEF:minActive={rrd1}:nginxActive:MIN \
         DEF:maxActive={rrd1}:nginxActive:MAX \
         AREA:avgActive#0000ff:"Active" \
         GPRINT:avgActive:AVERAGE:"Avg \\: %10.2lf %s" \
         GPRINT:minActive:MIN:"Min \\: %10.2lf %s" \
         GPRINT:maxActive:MAX:"Max \\: %10.2lf %s\\n"
         """