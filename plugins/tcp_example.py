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

class Example(Plugin):
    """
    This class is an example of a TCP server name Example,
    listening on port 1337.
    """

    def __init__(self, path):
        super(Example, self).__init__(path)

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
        self._xml_protocol_plugin = """
        <protocol-plugin protocol='Example'
            class-name='org.opennms.netmgt.capsd.plugins.TcpPlugin' scan='on'>
            <property value='1337' key='port'/>
            <property value='2000' key='timeout'/>
            <property value='1' key='retry'/>
        </protocol-plugin>
        """

        # Add a node 'service' to the file 'poller-configuration.xml'
        self._xml_service = """
        <service name="Example" interval="300000" user-defined="false"
            status="on">
            <parameter key="retry" value="1" />
            <parameter key="timeout" value="2200" />
            <parameter key="port" value="1337" />
        </service>
        """

        # Add a node 'monitor' to the file 'poller-configuration.xml'
        self._xml_monitor = """
        <monitor service="Example"
            class-name="org.opennms.netmgt.poller.monitors.TcpMonitor" />
        """