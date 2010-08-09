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

class Database(Plugin):
    def __init__(self, path, database, username, password, jdbc = "mysql"):
        super(Database, self).__init__(path)
        driver = "org.gjt.mm.mysql.Driver" if jdbc == "mysql" else \
                 "oracle.jdbc.driver.OracleDriver" if jdbc == "oracle-9.0.2.4" else \
                 "mssql.Driver" if jdbc == "mssql" else \
                 "postgresql.Driver" # if jdbc == "postgresql"
                      
        port = "3306" if jdbc == "mysql" else \
               "1521" if jdbc == "oracle-9.0.2.4" else \
               "1433" if jdbc == "mssql" else \
               "5432" # if jdbc == "postgresql"
               
        name = "MySQL" if jdbc == "mysql" else \
               "Oracle" if jdbc == "oracle-9.0.2.4" else \
               "MSSQL" if jdbc == "mssql" else \
               "PostgreSQL" # if jdbc == "postgresql"
               
        if jdbc == "oracle-9.0.2.4":
            jdbc = "oracle:thin"
            
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
        <protocol-plugin protocol="%(name)s-Connection-%(database)s" class-name="org.opennms.netmgt.capsd.plugins.JDBCPlugin" scan="on">
            <property key="user" value="%(username)s"/>
            <property key="password" value="%(password)s"/>
            <property key="retry" value="3"/>
            <property key="timeout" value="5000"/>
            <property key="driver" value="%(driver)s"/>
            <property key="url" value="jdbc:%(jdbc)s://OPENNMS_JDBC_HOSTNAME:%(port)s/%(database)s"/>
        </protocol-plugin>
        """ % vars()
        #jdbc:oracle:thin:@OPENNMS_JDBC_HOSTNAME:%(port)s:%(database)
        
        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_service = """
        <service name="%(name)s-Connection-%(database)s" user-defined="false" interval="6000" status="on">
            <parameter key="user" value="%(username)s"/>
            <parameter key="password" value="%(password)s"/>
            <parameter key="timeout" value="3000"/>
            <parameter key="driver" value="%(driver)s"/>
            <parameter key="url" value="jdbc:%(jdbc)s://OPENNMS_JDBC_HOSTNAME:%(port)s/%(database)s"/>
        </service>
        """ % vars()
        
        # Add a node 'service' to the file 'collectd-configuration.xml'
        self._xml_monitor = """
        <monitor service="%(name)s-Connection-%(database)s" class-name="org.opennms.netmgt.poller.monitors.JDBCMonitor"/>
        """ % vars()
        