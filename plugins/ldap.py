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

class Ldap(Plugin):
    def __init__(self, path):
        super(Ldap, self).__init__(path)

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
        <protocol-plugin protocol="LDAP" class-name="org.opennms.netmgt.capsd.plugins.LdapPlugin" scan="on">
            <property key="port" value="389" />
            <property key="timeout" value="3000" />
            <property key="retry" value="2" />
        </protocol-plugin>
        """

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_service = """
        <service name="LDAP" interval="300000" user-defined="false" status="on">
          <parameter key="port" value="389" />
          <parameter key="version" value="3" />
          <parameter key="searchbase" value="DC=example,DC=com" />
          <parameter key="searchfilter" value="OU=OpenNMS" />
          <parameter key="dn" value="CN=usersearch" />
          <parameter key="password" value="secret" />
          <parameter key="retry" value="2" />
          <parameter key="timeout" value="3000" />
        </service>
        """

        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_monitor = """
        <monitor service="LDAP" class-name="org.opennms.netmgt.poller.monitors.LdapMonitor"/>
        """