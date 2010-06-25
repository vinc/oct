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
import pickle
import re
import sys
import time
import unittest
import urllib2
import xml.dom.minidom

import lib.distrib
import lib.system

import params

##########################################
#       System Test Sequence Class       #
##########################################

class SystemTestSequenceFunctions(unittest.TestCase):
    def test_01_opennms_dependencies(self):
        self.assertTrue(lib.distrib.is_installed("opennms"),
                "opennms is not installed")
        self.assertTrue(lib.distrib.is_installed("opennms-contrib"),
                "opennms-contrib is not installed")
    def test_02_iplike_and_postgresql_compatiblity(self):
        distribution = lib.distrib.get_distrib()
        if distribution == "debian":
            # DPKG query for finding all versions of PostgreSQL
            infos = lib.distrib.dpkg_query("${Package}: ${Status}\n",
                                           "postgresql-[78]*")

            # Sed command for extracting the version installed on the system
            sed_cmd = ["s/postgresql-\([0-9]\).\([0-9]\): install ok " \
                       "installed/\\1\\2/",
                       "/postgresql-[0-9].[0-9]: unknown ok not-installed/d"]

            # Execute the command and extract the version
            postgresql_version = lib.system.sed(sed_cmd, infos)

            # DPKG query for finding all versions of IPLike
            infos = lib.distrib.dpkg_query("${Package}: ${Status}\n", "iplike*")

            # Sed command for extracting the version installed on the system
            sed_cmd = ["s/iplike-pgsql\([0-9]\+\): install ok installed/\\1/",
                       "/iplike-pgsql[0-9]\+: unknown ok not-installed/d"]

            # Execute the command and extract the version
            iplike_version = lib.system.sed(sed_cmd, infos)

            # Compare the two versions
            self.assertEqual(postgresql_version, iplike_version,
                    "IPLike's version is not compatible with PostgreSQL's")

    def test_03_opennms_is_running(self):
        retcode = lib.system.get_retcode_cmd(["/etc/init.d/opennms", "status"])
        self.assertEqual(retcode, 0, "OpenNMS is not running")

    def test_04_postgresql_is_running(self):
        retcode = lib.system.get_retcode_cmd(["/etc/init.d/postgresql* status"],
                                              None, True)
        self.assertEqual(retcode, 0, "PostgreSQL is not running")

    def test_05_gpproxy_plugin(self):
        plugin_exist = lib.system.is_file(
            "/usr/share/opennms/contrib/gpproxy.py")
        self.assertTrue(plugin_exist, "GPProxy plugin does not exist")
        version = lib.system.get_output_cmd(
            ["/usr/share/opennms/contrib/gpproxy.py", "--version"])
        self.assertEqual(version, "gpproxy.py 0.2\n",
                         "GPProxy plugin is not the last version")

##########################################
#    Regression Test Sequence Function   #
##########################################

class RegressionTestSequenceFunctions(unittest.TestCase):
    def int_cmp(self, before, after, name):
        self.assertEqual(before, after,
                         "The total of %s changed from %d to %d" \
                         % (name, before, after))
    def test_01_webgui_nodes(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.webgui_nodes,
                     present_configuration.webgui_nodes, "nodes")

    def test_02_webgui_interfaces(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.webgui_interfaces,
                     present_configuration.webgui_interfaces, "interfaces")

    def test_03_webgui_users(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.webgui_users,
                     present_configuration.webgui_users, "users")

    def test_04_webgui_groups(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.webgui_groups,
                     present_configuration.webgui_groups, "groups")

    def test_05_database_nodes(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.db_nodes,
                     present_configuration.db_nodes, "nodes")

    def test_06_database_interfaces(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.db_interfaces,
                     present_configuration.db_interfaces, "interfaces")

    def test_07_config_users(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.config_users,
                     present_configuration.config_users, "users")

    def test_08_config_groups(self):
        global previous_configuration
        global present_configuration
        self.int_cmp(previous_configuration.config_groups,
                     present_configuration.config_groups, "groups")


##########################################
#       OpenNMS State Configuration      #
##########################################

class OpenNMSState(object):
    """
    Class for storing all the usefull informations of OpenNMS's configuration
    state for the Regression Test Sequence.
    """
    def __init__(self):
        # Date from the last information collect
        self.date = None
        # Nomber of nodes visible in the Web GUI
        self.webgui_nodes = None
        # Number of interfaces visible in the Web GUI
        self.webgui_interfaces = None
        # Number of users visible in the Web GUI
        self.webgui_users = None
        # Number of groups visible in the Web GUI
        self.webgui_groups = None
        # Number of nodes contained in the database
        self.db_nodes = None
        # Number of interfaces contained in the database
        self.db_interfaces = None
        # Number of users defined on the configuration file
        self.config_users = None
        # Number of groups defined on the configuration file
        self.config_groups = None

    @classmethod
    def extract_from_uri(self, uri, pattern, group, count=False):
        """
        Return the result of the given regex on the given uri
        """
        # Build the HTTP request
        #print "GET '%s%s'" % (params.opennms_webgui_url, uri)
        req = lib.system.request_url(params.opennms_webgui_url + uri,
                                     params.opennms_webgui_username,
                                     params.opennms_webgui_password)
        try:
            url = urllib2.urlopen(req) # Send it to the server
        except urllib2.URLError, e:
            print >> sys.stderr, e
            exit(os.EX_IOERR)
        except:
            raise
        output = url.read() # Fetch the response
        url.close()
        p = re.compile(pattern)
        if count:
            return len(p.findall(output)) # Return the number of matches
        else:
            m = p.search(output)
            if m is not None:
                return m.group(group) # Return the first match
            else:
                return None # Return None if no matches

    @classmethod
    def count_from_db(self, db, query):
        """
        Count the number of row returned by the given query on the given db
        """
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM %s;" % query);
        result = int(cur.fetchone()[0])
        return result

    @classmethod
    def count_from_xml(self, filename, tag):
        """
        Count the occurence of the given tag in the xml file identified by
        the given filename
        """
        try:
            doc = xml.dom.minidom.parse("%s/%s" % (params.opennms_config_path, 
                                                   filename))
        except IOError, e:
            print >> sys.stderr, e
        except:
            raise
        else:
            return len(doc.getElementsByTagName(tag))

    def collect_informations(self):
        """
        Fill object with information from the Web GUI, database and XML
        configuration.
        """
        self.date = datetime.datetime.utcnow()
        # Collect infos from Web GUI
        self.webgui_nodes = int(self.extract_from_uri(
            "element/nodeList.htm",
            "[ \t]+(?P<nodes>[0-9]+) Nodes", "nodes"))
        self.webgui_interfaces = int(self.extract_from_uri(
            "element/nodeList.htm?listInterfaces=true",
            "[ \t]+[0-9]+ Nodes, (?P<interfaces>[0-9]+) Interfaces",
            "interfaces"))
        self.webgui_users = int(self.extract_from_uri(
            "admin/userGroupView/users/list.jsp",
            "[ \t]+<div id=\"users\((?P<users>\w+)\).fullName", "users", True))
        self.webgui_groups = int(self.extract_from_uri(
            "admin/userGroupView/groups/list.htm",
            "[ \t]+<a href=\"javascript:detailGroup\('(?P<groups>\w+)'\)\">",
            "groups", True))
        # Collect infos from database
        try:
            import psycopg2 as db2
        except ImportError:
            print >> sys.stderr, \
                "Module psycopg2 must be installed for collecting the" \
                "configuration state!"
            sys.exit(os.EX_UNAVAILABLE)
        try:
            db = db2.connect(database = params.opennms_db_name,
                             user = params.opennms_db_username,
                             password = params.opennms_db_password)
        except db2.DatabaseError, e:
            print >> sys.stderr, e
            sys.exit(os.EX_IOERR)
        self.db_nodes = self.count_from_db(db, "node")
        self.db_interfaces = self.count_from_db(db,
                "ipinterface WHERE ipaddr != '0.0.0.0'")
        # Collect infos from XML configuration
        self.config_users = self.count_from_xml("users.xml", "user")
        self.config_groups = self.count_from_xml("groups.xml", "group")

    def is_complete(self):
        """ Check if the object contain a complete configuration state """
        is_webgui_ok = self.webgui_nodes and self.webgui_interfaces and \
                       self.webgui_users and self.webgui_groups
        is_db_ok = self.db_nodes and self.db_interfaces
        is_config_ok = self.config_users and self.config_groups
        return self.date and is_webgui_ok and is_db_ok and is_config_ok

    def print_data(self):
        """ Print the configuration state in two column """
        fc_length = 35 # Length of the first column
        print "-" * 70
        print ""
        print "Saved date:".ljust(fc_length), \
              self.date.strftime("%a, %d %b %Y %H:%M:%S")
        print "Nodes (seen by the Web GUI):".ljust(fc_length), \
              self.webgui_nodes
        print "Nodes (in database):".ljust(fc_length), \
              self.db_nodes
        print "Interfaces (seen by the Web GUI):".ljust(fc_length), \
              self.webgui_interfaces
        print "Interfaces (in database):".ljust(fc_length), \
              self.db_interfaces
        print "Users (seen by the Web GUI):".ljust(fc_length), \
              self.webgui_users
        print "Users (in config file):".ljust(fc_length), \
              self.config_users
        print "Groups (seen by the Web GUI):".ljust(fc_length), \
              self.webgui_groups
        print "Groups (in config file):".ljust(fc_length), \
              self.config_groups
        print ""
        print "-" * 70

##########################################
#    Functions used in main function     #
##########################################

def run_test_sequence(tests, verb=0):
    if verb:
        print "-" * 70
    suite = unittest.TestLoader().loadTestsFromTestCase(tests)
    if verb > 1:
        print ""
    unittest.TextTestRunner(verbosity=verb).run(suite)


def default_config_file():
    i = 0
    default_file = "/tmp/opennms/tests-%s" % \
            datetime.datetime.now().strftime('%Y-%m-%d')
    # If the file exist,
    while lib.system.is_file("%s-%.3d.dump" % (default_file, i)):
        i += 1 # we must find another one
    return "%s-%.3d.dump" % (default_file, i)


##########################################
#             Main Function              #
##########################################

def main():
    global previous_configuration
    global present_configuration

    import params

    ##########################################
    #            Parse arguments             #
    ##########################################

    parser = optparse.OptionParser(usage="%prog [options]",
            version="%prog 0.1.2")
    system = optparse.OptionGroup(parser, 'System test')
    regression = optparse.OptionGroup(parser, 'Regression test')
    regression.add_option("-p", "--previous_config-file",
            help = "Load <filename> containing a previous configuration state",
            metavar = "<filename>",
            default = None)
    regression.add_option("-f", "--config-file",
            help = "Save the current configuration state to <filename>",
            metavar = "<filename>",
            default = None)
    parser.add_option("-v", "--verbose",
            help = "Increase verbosity level (use twice or more for "
                   "greater effect)",
            action = "count",
            dest = "verbosity")
    regression.add_option("-s", "--save",
            help = "Save the current configuration (to the default "
                   "location or somewhere specified by -f|--config-file)",
            action = "store_true")
    parser.add_option("-t", "--test-sequence",
            help = "Run \"system\" or \"regression\" test sequence",
            metavar = "<test_sequence>",
            choices = ["system", "regression"],
            default = None)

    parser.add_option_group(regression)
    (options, args) = parser.parse_args()

    # If --config_file is specified,
    if options.config_file and not options.save:
        options.save = True # Then --save is implicit.
    # If --config_file is not specified but --save is,
    elif options.save and not options.config_file:
        options.config_file = default_config_file() # use default file.

    if options.test_sequence == "regression" and not \
            options.previous_config_file:
        print >> sys.stderr, "No previous configuration file specifed!\n"
        parser.print_help()
        sys.exit(os.EX_USAGE)


    ##########################################
    #    Run System Test Sequence and exit   #
    ##########################################

    if options.test_sequence == "system":
        # Run the system tests
        print "Run the System Test Sequence..."
        run_test_sequence(SystemTestSequenceFunctions, options.verbosity)
        sys.exit(os.EX_OK)


    ##########################################
    #    Collect data for Regression Test    #
    ##########################################

    print "Collecting data for Regression Test Sequence..."
    present_configuration.collect_informations()
    if options.verbosity > 1:
        print "Present configuration:"
        present_configuration.print_data()
    present_configuration_have_been_used = False

    if options.save:
        present_configuration_have_been_used = True
        if lib.system.is_file(options.config_file):
            print >> sys.stderr, \
                "Cannot save to '%s', the file exist!" \
                % options.config_file
            sys.exit(os.EX_CANTCREAT)
        dirname = os.path.dirname(options.config_file)
        if not os.path.isdir(dirname):
            print >> sys.stderr, \
                "Cannot save to '%s'.\n" % options.config_file, \
                "The directory '%s' does not exist!" % dirname
            sys.exit(os.EX_OSFILE)
        f = open(options.config_file, 'wb')
        pickle.dump(present_configuration, f)
        print "The current configuration state " \
              "has been stored in '%s'." % options.config_file


    ##########################################
    # Load previous data for Regression Test #
    ##########################################
    if options.previous_config_file:
        print "Loading previous data for Regression Test Sequence..."
        try:
            f = open(options.previous_config_file, 'rb')
        except IOError, e:
            print >> sys.stderr, \
                     "Cannot load previous configuration state!\n", e
            sys.exit(os.EX_NOINPUT)

        previous_configuration = pickle.load(f)
        try:
            previous_configuration.is_complete()
        except (AttributeError, TypeError), e:
            print >> sys.stderr, \
                     "Some in formations are missing in the previous config " \
                     "file!\n", e
            sys.exit(os.EX_DATAERR)

        if options.verbosity > 1:
            print "Previous configuration:"
            previous_configuration.print_data()

    ##########################################
    #         Run Regression Sequence        #
    ##########################################

    if options.test_sequence == "regression":
        present_configuration_have_been_used = True

        # Run the regression tests
        print "Run the Regression Test Sequence..."
        run_test_sequence(RegressionTestSequenceFunctions, options.verbosity)

    if not present_configuration_have_been_used:
        print "What should we do with the collected data?"
        parser.print_help()

if __name__ == "__main__":

    ##########################################
    #             Fixed options              #
    ##########################################

    previous_configuration = OpenNMSState()
    present_configuration = OpenNMSState()

    main()
    sys.exit(os.EX_OK)