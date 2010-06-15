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

class Ntpd(Plugin):
    def __init__(self, path):
        super(Ntpd, self).__init__(path)

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
        <protocol-plugin protocol="Ntpd-Stats"
            class-name="org.opennms.netmgt.capsd.plugins.HttpPlugin" scan="on"
            user-defined="false">
            <property key="port" value="8080" />
            <property key="timeout" value="3000" />
            <property key="retry" value="2" />
            <property key="url" value="/ntpd_status" />
        </protocol-plugin>
        """

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_service = """
        <service name="Ntpd-Stats" interval="300000" user-defined="false"
            status="on">
            <parameter key="http-collection" value="ntpd-stats" />
            <parameter key="retry" value="1" />
            <parameter key="timeout" value="2000" />
            <parameter value='8080' key='port'/>
        </service>
        """

        # Add a node 'collector' to the file 'collectd-configuration.xml'
        self._xml_collector = """
        <collector service="Ntpd-Stats"
            class-name="org.opennms.netmgt.collectd.HttpCollector" />
        """

        # Add a node 'http-collection' to the file 'http-datacollection-config.xml'
        # Python requierement: '-' is replaced by '_' in the variable name
        self._xml_http_collection = """
        <http-collection name="Ntpd-Stats">
            <rrd step="300">
                <rra>RRA:AVERAGE:0.5:1:8928</rra>
                <rra>RRA:AVERAGE:0.5:12:8784</rra>
                <rra>RRA:MIN:0.5:12:8784</rra>
                <rra>RRA:MAX:0.5:12:8784</rra>
            </rrd>
            <uris>
                <uri name="ntpd">
                    <url path="/ntpd_status"
                        user-agent="OpenNMS HTTP Datacollection"
                        port="8080"
                        matches="(?s).*?([0-9]+)\s([0-9.-]+)\s([0-9.-]+)\s([0-9.-]+)\s([0-9.-]+)\s([0-9.-]+)\s([0-9]+).*" response-range="100-399">
                    </url>
                    <attributes>
                        <attrib alias="ntpdOffset" match-group="3" type="gauge32" />
                        <attrib alias="ntpdDrift" match-group="4" type="gauge32" />
                        <attrib alias="ntpdError" match-group="5" type="gauge32" />
                        <attrib alias="ntpdStability" match-group="6" type="gauge32" />
                    </attributes>
                </uri>
            </uris>
        </http-collection>
        """

        # Define a list of report graph we'll add to the configuration
        self._report_defs = ["ntpd.server.offset", "ntpd.server.drift"]

        # Define all the report graph
        # Python requierement: 'r' is needed before the string definition to
        # ensure the use of raw string to keep the return line.
        self._report_graph = r"""
        report.ntpd.server.offset.name=NTPd Offset
        report.ntpd.server.offset.columns=ntpdOffset, ntpdError
        report.ntpd.server.offset.type=nodeSnmp
        report.ntpd.server.offset.command=--title="NTPd Offset" \
         --vertical-label="Time (seconds)" \
         --lower-limit 0 \
         DEF:avgOffset={rrd1}:ntpdOffset:AVERAGE \
         DEF:minOffset={rrd1}:ntpdOffset:MIN \
         DEF:maxOffset={rrd1}:ntpdOffset:MAX \
         DEF:avgError={rrd2}:ntpdError:AVERAGE \
         DEF:minError={rrd2}:ntpdError:MIN \
         DEF:maxError={rrd2}:ntpdError:MAX \
         AREA:avgOffset#6699cc: \
         LINE1:avgOffset#000000:"Offset" \
         GPRINT:avgOffset:AVERAGE:"Avg \\: %6.2lf %s" \
         GPRINT:minOffset:MIN:"Min \\: %6.2lf %s" \
         GPRINT:maxOffset:MAX:"Max \\: %6.2lf %s\n" \
         LINE2:avgError#ffba00:"Error " \
         GPRINT:avgError:AVERAGE:"Avg \\: %6.2lf %s" \
         GPRINT:minError:MIN:"Min \\: %6.2lf %s" \
         GPRINT:maxError:MAX:"Max \\: %6.2lf %s\\n"

        report.ntpd.server.drift.name=NTPd Drift
        report.ntpd.server.drift.columns=ntpdDrift, ntpdStability
        report.ntpd.server.drift.type=nodeSnmp
        report.ntpd.server.drift.command=--title="NTPd Drift" \
         --vertical-label="Time (seconds)" \
         --lower-limit 0 \
         DEF:avgDrift={rrd1}:ntpdDrift:AVERAGE \
         DEF:minDrift={rrd1}:ntpdDrift:MIN \
         DEF:maxDrift={rrd1}:ntpdDrift:MAX \
         DEF:avgStability={rrd2}:ntpdStability:AVERAGE \
         DEF:minStability={rrd2}:ntpdStability:MIN \
         DEF:maxStability={rrd2}:ntpdStability:MAX \
         AREA:avgDrift#cc9966: \
         LINE1:avgDrift#000000:"Drift    " \
         GPRINT:avgDrift:AVERAGE:"Avg \\: %6.2lf %s" \
         GPRINT:minDrift:MIN:"Min \\: %6.2lf %s" \
         GPRINT:maxDrift:MAX:"Max \\: %6.2lf %s\n" \
         LINE2:avgStability#ffba00:"Stability" \
         GPRINT:avgStability:AVERAGE:"Avg \\: %6.2lf %s" \
         GPRINT:minStability:MIN:"Min \\: %6.2lf %s" \
         GPRINT:maxStability:MAX:"Max \\: %6.2lf %s\\n"
         """