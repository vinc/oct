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

import datetime
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
    backup_path = os.path.abspath(args[0])

    # Check if user is root (needed for database backup)
    if os.geteuid():
        print >> sys.stderr, \
        "Error: you cannot perform this operation unless you are root."
        exit(os.EX_NOPERM)

    # Create a sub backup directory for this backup
    if options.verbosity > 0:
        print
    print "Create the backup directory..."
    if not os.path.isdir(backup_path):
        sys.exit("Cannot open directory '%s': " \
                 "No such file or directory" % backup_path)
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    i = 0
    files_path = "%s/sav-%s-%.3d" % (backup_path, date, i)
    while os.path.isdir(files_path):
        i += 1
        files_path = "%s/sav-%s-%.3d" % (backup_path, date, i)
    os.umask(0)
    os.mkdir(files_path, 0777)
    print "OpenNMS will be backuped in '%s'." % files_path

    # Copy OpenNMS files
    if options.verbosity > 0:
        print
    print "Backup OpenNMS directory..."
    os.chdir(lib.system.get_parent_dir(options.opennms_path))
    cmd = ["/bin/tar", "--create", "--gzip", "--file",
           "%s/files.tar.gz" % files_path, "opennms"]
    if options.verbosity > 0:
        cmd.extend(["--verbose"])
    lib.system.exec_cmd(cmd, None, False, options.verbosity)

    # Copy OpenNMS configuration files
    if options.verbosity > 0:
        print
    print "Backup OpenNMS configuration directory..."
    os.chdir(lib.system.get_parent_dir(options.opennms_config_path))
    cmd = ["/bin/tar", "--create", "--gzip", "--dereference", "--file",
           "%s/config_files.tar.gz" % files_path, "etc"]
    if options.verbosity > 0:
        cmd.extend(["--verbose"])
    lib.system.exec_cmd(cmd, None, False, options.verbosity)

    # Dump OpenNMS database
    if options.verbosity > 0:
        print
    print "Backup OpenNMS database..."
    cmd = ["/bin/su",
           "--login", "postgres",
           "--command",
           "/usr/bin/pg_dump --create --username %s --format custom " \
           "--file %s/database.dump %s" \
           % (options.database_username, files_path, options.database_name)]
    lib.system.exec_cmd(cmd, None, False, options.verbosity)

if __name__ == "__main__":

    ##########################################
    #             Fixed options              #
    ##########################################

    main()
    sys.exit(os.EX_OK)
