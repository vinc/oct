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

class Syslog(Plugin):
    def __init__(self, path, server):
        super(Syslog, self).__init__(path)

        # List all modifications done to the configuration for this plugin.
        # 'self._list_xml_modifications' is a dict where each key is the name of
        # a node to add to a XML configuration file. The name of this file is
        # the value associated to the key.
        #
        # {nodename1: filename1, nodename2: filename2}
        self._list_xml_modifications = {
            "service": "service-configuration.xml",
            "configuration": "syslogd-configuration.xml",
        }
        # Add a node 'protocol-plugin' to the file 'capsd-configuration.xml'
        self._xml_service = """
        <service>
            <name>OpenNMS:Name=Syslogd</name>
            <class-name>org.opennms.netmgt.syslogd.jmx.Syslogd</class-name>
            <invoke at="start" pass="0" method="init"/>
            <invoke at="start" pass="1" method="start"/>
            <invoke at="status" pass="0" method="status"/>
            <invoke at="stop" pass="0" method="stop"/>
        </service>
        """ % vars()

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_configuration = """
        <configuration
            syslog-port="10514"
            new-suspect-on-message="false"
            forwarding-regexp="^((.+?) (.*))\n?$"
            matching-group-host="2"
            matching-group-message="3"
            discard-uei="DISCARD-MATCHING-MESSAGES"
            />
        """ % vars()
