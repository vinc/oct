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

import sys
import lib.distrib

################################################################################
# OpenNMS static parameters
#
# You may edit some of those parameters to fit your configuration
#

# Database parameters
opennms_db_name = "opennms"
opennms_db_username = "postgres"
opennms_db_password = ""

# Web GUI parameters
opennms_webgui_url = "http://localhost:8980/opennms/"
opennms_webgui_username = "admin"
opennms_webgui_password = "admin"

# Files path
opennms_path = "/usr/share/opennms"

################################################################################
#
# You should not have to edit anything above
#
opennms_script_version = "1.8.0"

unsupported_distribution = False
try:
    distribution = lib.distrib.get_distrib()
except ValueError:
    unsupported_distribution = True
else:
    if distribution == "debian":
        opennms_path = "/usr/share/opennms"
    elif distribution == "redhat":
        opennms_path = "/opt/opennms"
    else:
        unsupported_distribution = True
if unsupported_distribution:
    print "Warning: The current distribution is not supported by this script!"
opennms_config_path = "%s/etc" % opennms_path
