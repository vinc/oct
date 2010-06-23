#!/usr/bin/python
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

"""
History
Tested with:
    1.6.11 - Debian 5.0, CentOS 5.4
    1.7.10 - Debian 5.0, CentOS 5.4
    1.7.90 - Debian 5.0, Ubuntu 10.4
Bug:
    CentOS 5.4: RPM and Proxy
    Ubuntu 10.4: toxml() (not with Debian 5.0 nor ArchLinux)
"""

import optparse
import os
import re
import sys

import params
import lib.distrib
import lib.system

try:
    import psycopg2
    import psycopg2.extensions
except ImportError:
    print >> sys.stderr, "Error: module psycopg2 must be installed!"
    distribution = lib.distrib.get_distrib()
    if distribution == "debian":
        print "Try 'apt-get install python-psycopg2' for installing it."
    elif distribution == "redhat":
        print "Try 'yum install python-psycopg2' for installing it after " \
              "having added the RPMforge repository " \
              "('http://dag.wieers.com/rpm/FAQ.php#B2')."
    sys.exit(os.EX_SOFTWARE)


##########################################
#             Main Function              #
##########################################

def main():

    ##########################################
    #            Parse arguments             #
    ##########################################

    parser = optparse.OptionParser(usage = "%prog [options]",
                       version = "%prog 0.1.1")
    parser.add_option("-v", "--verbose",
        help="Increase verbosity level (use twice or more for greater effect)",
        action = "count",
        default = 0,
        dest = "verbosity")
    parser.add_option("-r", "--repository", \
        help = "Use \"stable\" or \"unstable\" for Debian and \"stable\", " \
               "\"testing\" or \"unstable\" for RedHat.",
        metavar = "<version>",
        choices = ["stable", "testing", "unstable"],
        default = "stable")
    parser.add_option("-n", "--number", \
        help = "Install the given version number.",
        metavar = "<digit>.<digit>.<digit>-<digit>",
        default = "")

    (options, args) = parser.parse_args()

    version = options.number

    if os.geteuid():
        print >> sys.stderr, \
        "Error: you cannot perform this operation unless you are root."
        exit(os.EX_NOPERM)

    # Fix OpenNMS's distribution specific folder
    opennms_path = None
    dialog = lambda d: \
        "This script will install OpenNMS %s on this %s based server." \
        % (options.repository.capitalize(), d)
    try:
        distribution = lib.distrib.get_distrib()
    except ValueError:
        sys.exit("Error: The current distribution is not supported by this " \
                 "script!")
    except:
        raise
    else:
        if distribution == "debian":
            opennms_path = "/usr/share/opennms"
            print dialog("Debian")
        elif distribution == "redhat":
            opennms_path = "/opt/opennms"
            print dialog("RedHat")
        else:
            sys.exit("Error: The %s distribution is not supported by this " \
                     "script!" % distribution)

    if lib.distrib.is_installed("opennms"):
        print "A version of OpenNMS have been detected on this system!"
        print "This script will overwrite the XML configuration files " \
              "and the database could be lost in the process too!"
        print "You should run 'backup.py' first..."
        rep = raw_input("Proceed with OpenNMS upgrade? [y/N] ")
        if not re.match("^[yY]([eE][sS])?$", rep):
            sys.exit(os.EX_OK)
    else:
        rep = raw_input("Proceed with OpenNMS installation? [Y/n] ")
        if not re.match("^([yY]([eE][sS])?)?$", rep):
            sys.exit(os.EX_OK)

    # Add OpenNMS Repository
    lib.distrib.add_repo(options.repository, options.verbosity)

    # Search the repo version and compare it with the script version.
    opennms_repo_version = \
        version if version != "" and distribution == "debian" \
        else lib.distrib.query_version("opennms")
    if lib.system.cmp_version(opennms_repo_version, 
                              params.opennms_script_version):
        print ""
        print >> sys.stderr, \
                 "Warning: this script was written for OpenNMS " \
                 "version %s but you are installing version %s!" % \
                 (opennms_script_version, opennms_repo_version)
        rep = raw_input("Continue anyway? [y/N] ")
        if not re.match("^[yY]([eE][sS])?$", rep):
            sys.exit(os.EX_OK)

    print ""
    print "Retrieving OpenNMS and his dependencies' packages..."
    if version != "" and distribution == "debian":
        packages = ["opennms", "opennms-db", "opennms-server",
                    "opennms-webapp-jetty", "opennms-common",
                    "libopennms-java", "libopennmsdeps-java"]
        lib.distrib.install(["%s=%s" % (p, version) for p in packages],
                            options.verbosity)
    else:
        lib.distrib.install(["opennms"], options.verbosity)

    if distribution == "redhat":
        # On Redhat based distribution, the config dir is empty after install
        print ""
        print "Starting PostgreSQL to let the configuration directory be " \
              "populated..."
        cmd = "/etc/init.d/postgresql* start"
        if options.verbosity == 0:
            cmd += " > /dev/null"
        lib.system.exec_cmd([cmd], "", True)

    print ""
    print "Stopping PostgreSQL..."
    cmd = "/etc/init.d/postgresql* stop"
    if options.verbosity == 0:
        cmd += " > /dev/null"
    lib.system.exec_cmd([cmd], "", True)

    print ""
    print "Modifying PostgreSQL's configuration..."
    # Search for the postgresql config file 'pg_hba.conf'
    postgresql_config_file = None
    postgresql_path = "/var/lib/pgsql/data/pg_hba.conf"
    if os.path.exists(postgresql_path):
        postgresql_config_file = postgresql_path
    else:
        postgresql_versions = [(i, j) for i in range(7,9) for j in range(5)]
        for i, j in postgresql_versions:
            postgresql_path = "/etc/postgresql/%d.%d/main/pg_hba.conf" % (i, j)
            if os.path.exists(postgresql_path):
                postgresql_config_file = postgresql_path
                # pass # Comment out for the older version on the system
    if postgresql_config_file is None:
        raise OSError("PostgreSQL's configuration file not found")
    # Backup the postgresql config file
    old_postgresql_config_file = lib.system.backup(postgresql_config_file)
    # Modify to allow postgres to connect (maybe not needed on debian)
    pattern = re.compile("(?P<auth>(local|host)\s+all\s+(all|postgres)" \
                         "(\s+[0-9.:/]+)?\s+)(ident( sameuser)?|md5)")
    try:
        old_f = open(old_postgresql_config_file, "r")
        new_f = open(postgresql_config_file, "w")
    except IOError, e:
        sys.exit(e)
    else:
        for line in old_f.readlines():
            m = pattern.match(line)
            if m is not None:
                new_f.write("%s%s\n" % (m.group("auth"), "trust"))
            else:
                new_f.write("%s" % line)
        old_f.close()
        new_f.close()


    print ""
    print "Starting PostgreSQL..."
    cmd = "/etc/init.d/postgresql* start"
    if options.verbosity == 0:
        cmd += " > /dev/null"
    lib.system.exec_cmd([cmd], "", True)

    print ""
    print "Creating OpenNMS's database..."
    try:
        lib.system.create_database("opennms", params.opennms_db_username,
                                   params.opennms_db_password)
    except psycopg2.OperationalError, e:
        #print >> sys.stderr, e # Could not connect, exit
        sys.exit(e)
    except psycopg2.ProgrammingError, e:
        print >> sys.stderr, e # Database already exists, pass
        pass
    except:
        raise

    print ""
    print "Installing IPLIKE..."
    if distribution == "debian":
        lib.system.exec_cmd(["/usr/sbin/install_iplike.sh"])
    elif distribution == "redhat":
        lib.distrib.install(["iplike"], options.verbosity)

    print ""
    print "Configuring JRE..."
    lib.system.exec_cmd(["%s/bin/runjava" % opennms_path, "-s"])

    print ""
    print "Fix a bug in OpenNMS Unstable installer for Debian..."
    if distribution == "debian" and options.repository == "unstable":
        # Bug with the installer, 'plpgsql' language doesn't exist in
        # OpenNMS database.
        try:
            lib.system.exec_cmd(["/usr/bin/createlang", "-U", "postgres",
                                 "plpgsql", "opennms"])
        except OSError:
            pass

    print ""
    print "Installing OpenNMS..."
    lib.system.exec_cmd(["%s/bin/install" % opennms_path, "-dis"])

    print ""
    print "Starting OpenNMS..."
    cmd = "/etc/init.d/opennms start"
    if options.verbosity == 0:
        cmd += " > /dev/null"
    try:
        lib.system.exec_cmd([cmd], "", True)
    except OSError:
        # Sometimes OpenNMS takes time to load, ignore this here
        pass

if __name__ == "__main__":

    ##########################################
    #             Fixed options              #
    ##########################################

    main()
    sys.exit(os.EX_OK)