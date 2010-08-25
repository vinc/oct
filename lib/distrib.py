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

import os
import re
import socket
import sys
import urllib2
import system

"""
This file contains some distribution specific functions used in the scripts
"""

def get_distrib():
    """
    Find out wich distribution is currently running this script.
    """
    operating_system = system.get_output_cmd(["/bin/uname",
                                              "--operating-system"])
    if re.search("GNU/Linux", operating_system):
        if os.path.exists("/etc/debian_version"):
            return "debian"
        elif os.path.exists("/etc/redhat-release"):
            return "redhat"
        else:
            raise ValueError("cannot find the current distribution")
    else:
        raise ValueError("cannot find the current operating system")

#def add_repo(version="stable", verbosity=0,
#             proxy_address=None, proxy_port=None,
#             proxy_username=None, proxy_password=None):
def add_repo(version="stable", verbosity=0):
    """
    Add OpenNMS repository stable, testing or unstable to the system according
    to the given version.
    Add repository signature and update the package database if required.
    """
    print "Adding OpenNMS %s repository..." % version
    distribution = get_distrib()
    if distribution == "debian":
        """
        In Debian there is two version of OpenNMS, the stable and the unstable
        version. We also have to add the according repository and OpenNMS's key
        to APT before resynchronizing his package index files.
        """
        assert version == "stable" or version == "unstable"
        try:
            f = open("/etc/apt/sources.list.d/opennms.list", "w")
        except IOError, e:
            sys.exit(e)
        except:
            raise
        else:
            f.write("# OpenNMS %s repository\n" % version)
            f.write("deb http://debian.opennms.org %s main\n" % version)
            f.write("deb-src http://debian.opennms.org %s main\n" % version)
            f.close()
        print ""
        print "Retrieving OpenNMS Repository's key..."
        """
        if proxy_address and proxy_port and proxy_username and proxy_password:
            if verbosity > 1:
                print "Using proxy '%s:%s'" % (proxy_address, proxy_port)
            proxy_handler = urllib2.ProxyHandler({'http': 'http://%s:%s@%s:%s' \
                % (proxy_username, proxy_password, proxy_address, proxy_port)})
            opener = urllib2.build_opener(proxy_handler)
            urllib2.install_opener(opener)
        """
        # In Python < 2.6 there is no timeout for urllib2.urlopen()
        default_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(5) # so we have to fixe one
        uri = "http://debian.opennms.org/OPENNMS-GPG-KEY"
        try:
            url = urllib2.urlopen(uri) # Get the repository key
        except urllib2.URLError, e:
            sys.exit("Failed to connect to '%s': %s" % (uri, e))
        socket.setdefaulttimeout(default_timeout)
        key = ""
        for line in url.readlines(): # Read the repository key
            key += line
        if verbosity > 1:
            print key
        print "Exporting the key to APT keyring..."
        system.exec_cmd(["/usr/bin/apt-key", "add", "-"], key)
        print
        print "Updating the system..."
        cmd = ["/usr/bin/apt-get", "update", "--yes"]
        if verbosity == 0:
            cmd.extend(["--quiet", "2"])
        elif verbosity == 1:
            cmd.extend(["--quiet", "1"])
        system.exec_cmd(cmd)
    elif distribution == "redhat":
        assert version == "stable" or version == "testing" or \
               version == "unstable"
        cmd = ["/bin/rpm", "--upgrade",
               "http://yum.opennms.org/repofiles/" \
               "opennms-repo-%s-rhel5.noarch.rpm" % version]
        if verbosity > 0:
            cmd.extend(["--verbose", "--hash"])
        if verbosity > 1:
            cmd.extend(["--verbose"])
        system.exec_cmd(cmd)
    else:
        raise ValueError("cannot add OpenNMS Repository to the current " \
                         "distribution")

def install(packages, verbosity):
    distribution = get_distrib()
    cmd = list()
    if distribution == "debian":
        os.putenv("SKIP_IPLIKE_INSTALL", "1")
        system.exec_cmd(["/usr/bin/debconf-set-selections"],
                   "sun-java6-jre shared/accepted-sun-dlj-v1-1 select true")
        cmd.extend(["/usr/bin/apt-get", "install", "--assume-yes", "--force-yes"])
        # "--force-yes" is not a good idea... Used during upgrade.
        if verbosity == 0:
           cmd.extend(["--quiet", "2"])
        elif verbosity == 1:
          cmd.extend(["--quiet", "1"])
    elif distribution == "redhat":
        cmd.extend(["/usr/bin/yum", "install", "-y"])
        #if verbosity == 0:
        #   cmd.extend(["--quiet"])
        if verbosity > 1:
          cmd.extend(["--verbose"])
    cmd.extend(packages)
    system.exec_cmd(cmd, verbosity=verbosity)


def dpkg_query(info, regex):
	"""
    Get the given information concerning all package matching the given regex.
    """
	return system.get_output_cmd(["/usr/bin/dpkg-query",
		"--show",
		"--showformat", info,
		regex])

def is_installed(package):
    """ Get the status of the given package """
    #return dpkg_query("${Status}", package)
    distribution = get_distrib()
    if distribution == "debian":
        cmd = ["/usr/bin/dpkg-query", "--show", "--showformat", "${Status}",
               package]
    elif distribution == "redhat":
        cmd = ["/bin/rpm", "--query", package]
    else:
        raise ValueError("cannot find the current distribution")
    output = system.get_output_cmd(cmd)
    if distribution == "debian":
        return output == "install ok installed"
    elif distribution == "redhat":
        if re.match("package \w+ is not installed", package):
            return False
        else:
            return True

def query_version(package):
    """ Get the version of the given package """
    distribution = get_distrib() # Choose the appropriate package query tool
    if distribution == "debian":
        cmd = ["/usr/bin/apt-cache", "show", package]
    elif distribution == "redhat":
        cmd = ["/usr/bin/yum", "--quiet", "info", package]
    else:
        raise ValueError("cannot find the current distribution")
    output = system.get_output_cmd(cmd) # Retrieve package informations
    pattern = re.compile("Version[ \t]*:[ \t]+(?P<version>[0-9.]+)")
    m = pattern.search(output) # Extract package version
    if m:
        return m.group("version")
    else:
        raise ValueError("cannot find OpenNMS version")
        return None

