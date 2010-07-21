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

class Mail(Plugin):
    def __init__(self, path):
        super(Mail, self).__init__(path)

        # List all modifications done to the configuration for this plugin.
        # 'self._list_xml_modifications' is a dict where each key is the name of
        # a node to add to a XML configuration file. The name of this file is
        # the value associated to the key.
        #
        # {nodename1: filename1, nodename2: filename2}
        self._list_xml_modifications = {
            "service": "poller-configuration.xml",
            "monitor": "poller-configuration.xml",
        }

        # Add a node 'service' to the file 'pollerd-configuration.xml'
        self._xml_service = """
        <service name="Mail-Transport" interval="300000" user-defined="false" status="on">
            <parameter key="retry" value="5"/>
            <parameter key="mail-transport-test">
                <mail-transport-test>
                    <mail-test>
                        <sendmail-test attempt-interval="3000" use-authentication="false" use-jmta="false">
                            <sendmail-host host="${ipaddr}" port="25" />
                            <sendmail-protocol mailer="smtpsend" />
                            <sendmail-message 
		        to="opennms@example.com" 
		        from="opennms@example.com" 
		        subject="OpenNMS - Poller Test"
                                body="This is an OpenNMS test message." />
                            <user-auth user-name="opennms" password="secret" />
                        </sendmail-test>
                        <readmail-test attempt-interval="60000" mail-folder="INBOX" subject-match="OpenNMS - Poller Test" >
                            <readmail-host host="mail.example.com" port="143">
                                <readmail-protocol ssl-enable="false" start-tls="false" transport="imap" />
                            </readmail-host>
                            <user-auth user-name="opennms" password="secret"/>
                        </readmail-test>
                    </mail-test>
                </mail-transport-test>
            </parameter>
        </service>
        """

        # Add a node 'service' to the file 'pollerd-configuration.xml'
        self._xml_monitor = """
        <monitor service="Mail-Transport" class-name="org.opennms.netmgt.poller.monitors.MailTransportMonitor" />
        """