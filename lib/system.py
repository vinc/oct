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
import subprocess
import sys
import shutil
import urllib2
import base64

"""
This library contains some system command wrapper
"""

def create_database(name, username, password):
    """
    Create a database named "name" with the creditentials of "username".
    This function need "psycopg2" module.
    """
    _manage_database("CREATE", name, username, password)

def drop_database(name, username, password):
    """
    Create a database named "name" with the creditentials of "username".
    This function need "psycopg2" module.
    """
    _manage_database("DROP", name, username, password)

def _manage_database(action, name, username, password):
    try:
        import psycopg2
        import psycopg2.extensions
    except ImportError:
        print >> sys.stderr, "Error: module psycopg2 must be installed!"
        distribution = distrib.get_distrib()
        if distribution == "debian":
            print "Try 'apt-get install python-psycopg2' for installing it."
        elif distribution == "redhat":
            print "Try 'yum install python-psycopg2' for installing it after " \
                  "having added the RPMforge repository " \
                  "('http://dag.wieers.com/rpm/FAQ.php#B2')."
    conn = psycopg2.connect(user=username, password=password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute("%s DATABASE %s" % (action, name))
    except psycopg2.OperationalError:
        sys.exit("Database operational error: is OpenNMS running?")
    except:
        raise

def get_retcode_cmd(cmd, input=None, use_shell=False):
    """
    Execute the given "cmd" command with the optionnal input pipe and return
    its return code.
    """
    return subprocess.call(cmd,
        stdin=input,
        stdout=open('/dev/null', 'w'),
        shell=use_shell)

def get_output_cmd(cmd, input_pipe=None):
    """
    Execute the given "cmd" command with the optionnal input pipe and return
    its output.
    """
    p = subprocess.Popen(cmd,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return p.communicate(input=input_pipe)[0]

def exec_cmd(cmd, str_input=None, use_shell=False, verbosity=0):
    """
    Execute the given "cmd" command with the optionnal input string.
    """
    if verbosity > 2:
        print "Debug: executing '%s'..." % " ".join(cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=use_shell)
    p.communicate(input=str_input)
    if p.returncode:
        raise OSError("error: the child return code (%d) is not null" \
                      % p.returncode)
	
def request_url(uri, username=None, password=None):
    if username and password:
        #TODO: dont use this, "http://username:password@uri" do the same
        credentials = base64.b64encode("%s:%s" % (username, password))
        headers = {"Authorization" : "Basic %s" % credentials}
    else:
        headers = None
    return urllib2.Request(uri, None, headers)

def is_file(filename):
    """
    Return True if filename can be opened, False otherwise
    """
    try:
        f = open(filename)
        f.close()
        return True
    except IOError, e:
        return False

def sed(scripts, input_pipe=None):
    #TODO: dont use this, import re!
	sed_cmd = ["/bin/sed"]
	for script in scripts:
		sed_cmd.extend(["-e", script])
	return get_output_cmd(sed_cmd, input_pipe)

def backup(filename):
    """
    Backup a file without overwritting previous backup and
    return the backup name.
    """
    backupname = "%s.old" % filename
    i = 0
    while os.path.exists(backupname):
        backupname = "%s.old.%d" % (filename, i)
        i += 1
    shutil.copy2(filename, backupname)
    return backupname

def get_parent_dir(path):
    parent_level = len(path.split("/")) - 1
    return "/".join(path.split("/")[:parent_level])
    
def cmp_version(str_first, str_second):
    """
    Compare two string containing a package or software version number defined
    number separated by something else.
    Examples: "0.1.6" => [0, 1, 6], "1.23RC1" => [1, 23, 1]
    """
    list_str_first = re.split("\D+", str_first)
    list_str_second = re.split("\D+", str_second)
    list_int_first = list()
    for num in list_str_first:
        list_int_first.append(int(num))
    list_int_second = list()
    for num in list_str_second:
        list_int_second.append(int(num))
    return list_int_first > list_int_second