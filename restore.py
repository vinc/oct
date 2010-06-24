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

import optparse
import os
import sys

import params
import lib.system

##########################################
#             Main Function              #
##########################################

def main():

	##########################################
	#            Parse arguments             #
	##########################################

    parser = optparse.OptionParser(usage="%prog [options] <backup-path>",
                                   version="%prog 0.1.1")
    parser.add_option("-i", "--opennms-path",
        help = "Change the default path from %s to the given path." % \
        params.opennms_path,
        metavar = "<path>",
        default = params.opennms_path)
    parser.add_option("-c", "--opennms-config-path",
        help = "Change the default config path from %s to the given path." % \
        params.opennms_config_path,
        metavar = "<path>",
        default = params.opennms_config_path)
    parser.add_option("-d", "--database-name",
        help = "Change the default database name from %s to the given name." % \
        params.opennms_db_name,
        metavar = "<name>",
        default = params.opennms_db_name)
    parser.add_option("-u", "--database-username",
        help = "Change the default database username from %s to the given " \
               "username." % params.opennms_db_username,
        metavar = "<username>",
        default = params.opennms_db_username)
    parser.add_option("-p", "--database-password",
        help = "Change the default database password to the given " \
               "password.",
        metavar = "<password>",
        default = "")
    parser.add_option("-v", "--verbose",
        help = "Increase verbosity level (use twice or more for greater " \
               "effect).",
        action = "count",
        dest = "verbosity")

    (options, args) = parser.parse_args()

    # Look for the backup directory
    nb_args = 1
    if len(args) != nb_args:
        sys.exit("%d argument(s) given, %d requiered!\n" % (len(args), nb_args))
    backup_path = args[0]

    # Copy OpenNMS files
    if options.verbosity > 0:
        print
    print "Restore OpenNMS directory..."
    if not os.path.isfile("%s/files.tar.gz" % backup_path):
        sys.exit("Cannot open directory '%s/files.tar.gz': " \
                 "No such file or directory" % backup_path)
    os.chdir(lib.system.get_parent_dir(options.opennms_path))
    cmd = ["/bin/tar", "--extract", "--gzip", "--file",
           "%s/files.tar.gz" % backup_path]
    if options.verbosity > 0:
        cmd.extend(["--verbose"])
    lib.system.exec_cmd(cmd, None, False, options.verbosity)

    # Copy OpenNMS configuration files
    if options.verbosity > 0:
        print
    print "Restore OpenNMS configuration directory..."
    if not os.path.isfile("%s/config_files.tar.gz" % backup_path):
        sys.exit("Cannot open directory '%s/config_files.tar.gz': " \
                 "No such file or directory" % backup_path)
    os.chdir(lib.system.get_parent_dir(options.opennms_config_path))
    cmd = ["/bin/tar", "--extract", "--gzip", "--file",
           "%s/config_files.tar.gz" % backup_path]
    if options.verbosity > 0:
        cmd.extend(["--verbose"])
    lib.system.exec_cmd(cmd, None, False, options.verbosity)

    # Restore OpenNMS database
    if options.verbosity > 0:
        print
    print "Restore OpenNMS database..."
    try:
        lib.system.drop_database(options.database_name,
                                 options.database_username,
                                 options.database_password)
    except:
        raise
    lib.system.create_database(options.database_name,
                               options.database_username,
                               options.database_password)
    print "--"
    if not os.path.isfile("%s/database.dump" % backup_path):
        sys.exit("Cannot open directory '%s/database.dump': " \
                 "No such file or directory" % backup_path)
    cmd = ["/bin/su",
           "--login", "postgres",
           "--command",
           "/usr/bin/pg_restore --username %s --clean --dbname %s " \
           "%s/database.dump"  \
           % (options.database_username, options.database_name, backup_path)]
    try:
        lib.system.exec_cmd(cmd, None, False, options.verbosity)
    except OSError:
        #ignore warnings
        pass
    except:
        raise

if __name__ == "__main__":
    ##########################################
    #             Fixed options              #
    ##########################################

    main()
    sys.exit(os.EX_OK)
