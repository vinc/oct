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

class Oracle_Instance_Linux(Plugin):
    def __init__(self, path, name, value, run_level = 2):
        super(Oracle_Instance_Linux, self).__init__(path)

        # List all modifications done to the configuration for this plugin.
        # 'self._list_xml_modifications' is a dict where each key is the name of
        # a node to add to a XML configuration file. The name of this file is
        # the value associated to the key.
        #
        # {nodename1: filename1, nodename2: filename2}
        self._list_xml_modifications = {
            "protocol-plugin": "capsd-configuration.xml",
            "service": "poller-configuration.xml",
            "monitor": "poller-configuration.xml",
        }
        # Add a node 'protocol-plugin' to the file 'capsd-configuration.xml'
        # <specific>192.168.0.42</specific>
        self._xml_protocol_plugin = """
        <protocol-plugin protocol="Oracle-Instance-%(name)s"
            class-name="org.opennms.netmgt.capsd.plugins.HostResourceSwRunPlugin"
            scan="on" user-defined="false">
            <property key="timeout" value="2000" />
            <property key="retry" value="1" />
            <property key="service-name-oid" value=".1.3.6.1.2.1.25.4.2.1.4" />
            <property key="service-name" value="%(value)s" />
        </protocol-plugin>
        """ % vars()

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_service = """
        <service name="Oracle-Instance-%(name)s" interval="300000" 
            user-defined="false" status="on">
            <parameter key="retry" value="1" />
            <parameter key="timeout" value="3000" />
            <parameter key="service-name-oid" value=".1.3.6.1.2.1.25.4.2.1.4" />
            <parameter key="service-name" value="%(value)s" />
            <parameter key="match-all" value="true" />
        </service>
        """ % vars()

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_monitor = """
        <monitor service="Oracle-Instance-%(name)s" 
           class-name="org.opennms.netmgt.poller.monitors.HostResourceSwRunMonitor" />
        """ % vars()