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

class Apache(Plugin):
    def __init__(self, path):
        super(Apache, self).__init__(path)

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
        <protocol-plugin protocol="Apache-Stats"
            class-name="org.opennms.netmgt.capsd.plugins.HttpPlugin" scan="on"
            user-defined="false">
            <property key="port" value="80" />
            <property key="timeout" value="3000" />
            <property key="retry" value="2" />
            <property key="url" value="/server-status/?auto" />
        </protocol-plugin>
        """

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_service = """
        <service name="Apache-Stats" interval="300000" user-defined="false"
            status="on" >
            <parameter key="http-collection" value="apache-stats" />
            <parameter key="retry" value="1" />
            <parameter key="timeout" value="2000" />
        </service>
        """

        # Add a node 'collector' to the file 'collectd-configuration.xml'
        self._xml_collector = """
        <collector service="Apache-Stats"
            class-name="org.opennms.netmgt.collectd.HttpCollector" />
        """

        # Add a node 'http-collection' to the file 'http-datacollection-config.xml'
        # Python requierement: '-' is replaced by '_' in the variable name
        self._xml_http_collection = """
        <http-collection name="Apache-Stats">
            <rrd step="300">
                <rra>RRA:AVERAGE:0.5:1:8928</rra>
                <rra>RRA:AVERAGE:0.5:12:8784</rra>
                <rra>RRA:MIN:0.5:12:8784</rra>
                <rra>RRA:MAX:0.5:12:8784</rra>
            </rrd>
            <uris>
                <uri name="apache">
                    <url path="/server-status/?auto"
                        user-agent="OpenNMS HTTP Datacollection"
                        matches="(?s).*?Total\sAccesses:\s([0-9]+).*?Total\skBytes:\s([0-9]+).*?CPULoad:\s([0-9\.]+).*?Uptime:\s([0-9]+).*?ReqPerSec:\s([0-9\.]+).*?BytesPerSec:\s([0-9\.]+).*?BytesPerReq:\s([0-9\.]+).*?BusyWorkers:\s([0-9]+).*?IdleWorkers:\s([0-9]+).*" response-range="100-399" >
                    </url>
                    <attributes>
                        <attrib alias="TotalAccesses" match-group="1" type="gauge32"/>
                        <attrib alias="TotalkBytes" match-group="2" type="gauge32"/>
                        <attrib alias="CPULoad" match-group="3" type="gauge32"/>
                        <attrib alias="Uptime" match-group="4" type="gauge32"/>
                        <attrib alias="ReqPerSec" match-group="5" type="gauge32"/>
                        <attrib alias="BytesPerSec" match-group="6" type="gauge32"/>
                        <attrib alias="BytesPerReq" match-group="7" type="gauge32"/>
                        <attrib alias="BusyWorkers" match-group="8" type="gauge32"/>
                        <attrib alias="IdleWorkers" match-group="9" type="gauge32"/>
                    </attributes>
                </uri>
            </uris>
        </http-collection>
        """

        # Define a list of report graph we'll add to the configuration
        self._report_defs = ["apache.workers", "apache.bytes", "apache.uptime",
                             "apache.cpu", "apache.access", "apache.kbytes",
                             "apache.byteperreq", "apache.reqpersec"]

        # Define all the report graph
        # Python requierement: 'r' is needed before the string definition to
        # ensure the use of raw string to keep the return line.
        self._report_graph = r"""
        report.apache.workers.name=Apache HTTP Workers
        report.apache.workers.columns=BusyWorkers,IdleWorkers
        report.apache.workers.type=nodeSnmp
        report.apache.workers.command=--title="Apache HTTP workers" \
         --vertical-label workers \
         DEF:BusyWorkers={rrd1}:BusyWorkers:AVERAGE \
         DEF:IdleWorkers={rrd2}:IdleWorkers:AVERAGE \
         LINE2:BusyWorkers#ff0000:"busy workers " \
         GPRINT:BusyWorkers:AVERAGE:"Avg  \\: %8.2lf %s" \
         GPRINT:BusyWorkers:MIN:"Min  \\: %8.2lf %s" \
         GPRINT:BusyWorkers:MAX:"Max  \\: %8.2lf %s\\n" \
         LINE2:IdleWorkers#00ff00:"idle workers " \
         GPRINT:IdleWorkers:AVERAGE:"Avg  \\: %8.2lf %s" \
         GPRINT:IdleWorkers:MIN:"Min  \\: %8.2lf %s" \
         GPRINT:IdleWorkers:MAX:"Max  \\: %8.2lf %s\\n"

        report.apache.bytes.name=Apache Bytes Per Second
        report.apache.bytes.columns=BytesPerSec
        report.apache.bytes.type=nodeSnmp
        report.apache.bytes.command=--title="Apache HTTP Bytes Per Second" \
         --vertical-label Bytes \
         DEF:BytesPerSec={rrd1}:BytesPerSec:AVERAGE \
         AREA:BytesPerSec#66CCFF: \
         LINE1:BytesPerSec#000000:"Bytes per second " \
         GPRINT:BytesPerSec:AVERAGE:"Avg  \\: %8.2lf %s" \
         GPRINT:BytesPerSec:MIN:"Min  \\: %8.2lf %s" \
         GPRINT:BytesPerSec:MAX:"Max  \\: %8.2lf %s\\n"

        report.apache.uptime.name=Apache Uptime
        report.apache.uptime.columns=Uptime
        report.apache.uptime.type=nodeSnmp
        report.apache.uptime.command=--title="Apache HTTP Uptime" \
         --vertical-label UpTime \
         --units-exponent 0 \
         DEF:Uptime={rrd1}:Uptime:AVERAGE \
         CDEF:timesec=Uptime,1,* \
         CDEF:timemin=timesec,60,/ \
         CDEF:timehour=timemin,60,/ \
         CDEF:timeday=timehour,24,/ \
         AREA:timehour#CC99FF: \
         LINE1:timehour#000000:"Hours" \
         GPRINT:timehour:MIN:"Min  \\: %8.2lf" \
         GPRINT:timehour:MAX:"Max  \\: %8.2lf\\n" \
         AREA:timeday#33FF00: \
         LINE1:timeday#33FF00:"Days" \
         GPRINT:timeday:MIN:"Min  \\: %8.2lf" \
         GPRINT:timeday:MAX:"Max  \\: %8.2lf\\n"

        report.apache.cpu.name=Apache Cpu Load
        report.apache.cpu.columns=CPULoad
        report.apache.cpu.type=nodeSnmp
        report.apache.cpu.command=--title="Apache Cpu Load" \
         --vertical-label Load \
         DEF:CPULoad={rrd1}:CPULoad:AVERAGE \
         AREA:CPULoad#999999: \
         LINE1:CPULoad#000000:"Load" \
         GPRINT:CPULoad:AVERAGE:"Avg  \\: %8.2lf%%" \
         GPRINT:CPULoad:MIN:"Min  \\: %8.2lf%%" \
         GPRINT:CPULoad:MAX:"Max  \\: %8.2lf%%\\n"

        report.apache.access.name=Apache Accesses
        report.apache.access.columns=TotalAccesses
        report.apache.access.type=nodeSnmp
        report.apache.access.command=--title="Apache Total Accesses" \
         --vertical-label Number \
         DEF:TotalAccesses={rrd1}:TotalAccesses:AVERAGE \
         AREA:TotalAccesses#FF6600: \
         LINE1:TotalAccesses#000000:"Total Accesses" \
         GPRINT:TotalAccesses:AVERAGE:"Avg  \\: %8.2lf %s" \
         GPRINT:TotalAccesses:MIN:"Min  \\: %8.2lf %s" \
         GPRINT:TotalAccesses:MAX:"Max  \\: %8.2lf %s\\n"

        report.apache.kbytes.name=Apache Total kBytes
        report.apache.kbytes.columns=TotalkBytes
        report.apache.kbytes.type=nodeSnmp
        report.apache.kbytes.command=--title="Apache Total kBytes" \
         --vertical-label kBytes \
         DEF:TotalkBytes={rrd1}:TotalkBytes:AVERAGE \
         AREA:TotalkBytes#00cc00: \
         LINE1:TotalkBytes#000000:"Total kBytes" \
         GPRINT:TotalkBytes:AVERAGE:"Avg  \\: %8.2lf %s" \
         GPRINT:TotalkBytes:MIN:"Min  \\: %8.2lf %s" \
         GPRINT:TotalkBytes:MAX:"Max  \\: %8.2lf %s\\n"

        report.apache.byteperreq.name=Apache Bytes Per Request
        report.apache.byteperreq.columns=BytesPerReq
        report.apache.byteperreq.type=nodeSnmp
        report.apache.byteperreq.command=--title="Apache Bytes Per Request" \
         --vertical-label Bytes \
         DEF:BytesPerReq={rrd1}:BytesPerReq:AVERAGE \
         AREA:BytesPerReq#9999CC: \
         LINE1:BytesPerReq#000000:"Bytes Per Request" \
         GPRINT:BytesPerReq:AVERAGE:"Avg  \\: %8.2lf %s" \
         GPRINT:BytesPerReq:MIN:"Min  \\: %8.2lf %s" \
         GPRINT:BytesPerReq:MAX:"Max  \\: %8.2lf %s\\n"

        report.apache.reqpersec.name=Apache Requests Per Second
        report.apache.reqpersec.columns=ReqPerSec
        report.apache.reqpersec.type=nodeSnmp
        report.apache.reqpersec.command=--title="Apache Requests Per Second" \
         --vertical-label Requests \
         DEF:ReqPerSec={rrd1}:ReqPerSec:AVERAGE \
         AREA:ReqPerSec#009999: \
         LINE1:ReqPerSec#000000:"Requests Per Second" \
         GPRINT:ReqPerSec:AVERAGE:"Avg  \\: %8.2lf %s" \
         GPRINT:ReqPerSec:MIN:"Min  \\: %8.2lf %s" \
         GPRINT:ReqPerSec:MAX:"Max  \\: %8.2lf %s\\n"
         """