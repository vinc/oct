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

import re
import fileinput
import sys
from lib.xmlfile import XMLFile
import xml.dom.minidom

from StringIO import StringIO

class Plugin(object):
    """
    A Plugin object contains some piece of information to add or substact
    from Opennms configuration.
    """

    def __init__(self, path):
        self._path = path

        # A new plugin who inherite from this class should define the following
        # attributes (see 'apache.py' for example):
        self._list_xml_modifications = dict()
        self._report_defs = list()
        self._report_graph = r""

        # Graphical report plugin definition
        self._report_var = "[a-zA-Z0-9-.]+"
        self._report_sep = "[, ]+"
        self._report_line = r"(%s%s)+\\?\n" % (self._report_var,
                                                 self._report_sep)
        self._report_first_line = r"reports=%s" % self._report_line
        self._report_last_line = r"(%s%s)*%s\n" % (self._report_var,
                                                   self._report_sep,
                                                   self._report_var)

    def _is_part_of_report(self, line, previous_line_was_part_of_report_report):
        return True if re.match(self._report_first_line, line) is not None \
                    else True if previous_line_was_part_of_report_report and \
                                 re.match(self._report_line, line) is not None \
                    else True if previous_line_was_part_of_report_report and \
                                 self._is_last_line_of_report(line) \
                    else False

    def _is_last_line_of_report(self, line):
        """
        pattern = self._report_last_line
        p = .compile()
        ret = re.match(pattern, line)
        if ret is not None:
            return True
        else:
            return False
        """
        return re.match(self._report_last_line, line) is not None

    def enable(self, simulate_only = True):
        print "Loading plugin '%s' ..." % self.__class__.__name__
        for node_name in self._list_xml_modifications.keys():
            # Load the XML configuration tree
            xml_file = "%s/%s" % (self._path,
                                  self._list_xml_modifications[node_name])
            if self.verbosity > 1:
                print "\tAdding node '%s' to '%s' ..." % (node_name, xml_file)

            config = XMLFile.open(xml_file, "w")

            # Try to find the node's parent in it
            nodes = config.get_document().getElementsByTagName(node_name)
            if nodes.length:
                parent = nodes.item(0).parentNode
            else:
                parent = config.get_root()
            # Load the XML tree of the node content
            node_ref = "_xml_%s" % node_name.replace("-", "_")
            node_xml = getattr(self, node_ref)
            doc_plugin = xml.dom.minidom.parseString(node_xml)
            node = doc_plugin.getElementsByTagName(node_name).item(0)
            # Merge it with the configuration tree
            parent.appendChild(node)
            if not simulate_only:
                # Write the modifications
                config.write()

        if hasattr(self, "_report_defs") and hasattr(self, "_report_graph"):
            # Add graph definition
            graph_file = "%s/snmp-graph.properties" % self._path
            if self.verbosity > 1:
                print "\tAdding graph in '%s' ..." % graph_file
            # Is the current line part of the report graph declaration?
            line_is_rep_dec = False
            for line in fileinput.input(graph_file, inplace=1):
                # In the first part of the file are declared the graph's names
                # We have to add those from 'self._report_defs'
                line_is_rep_dec = self._is_part_of_report(line, line_is_rep_dec)
                if line_is_rep_dec and self._is_last_line_of_report(line):
                    new_line = ""
                    for report_plugin_variable in self._report_defs:
                        new_line += "%s, " % report_plugin_variable
                    new_line += "\\\n"
                    if not simulate_only:
                        sys.stdout.write(new_line)
                # Add the graph content just before the last line
                if "EOF" in line:
                    sys.stdout.write(self._report_graph)
                    sys.stdout.write("\n")
                sys.stdout.write(line)

    def disable(self, simulate_only = True):
        if self.verbosity > 1:
                print "Unloading plugin '%s' ..." % self.__class__.__name__
        for node_name in self._list_xml_modifications.keys():
            # Load the XML configuration tree
            xml_file = "%s/%s" % (self._path,
                                  self._list_xml_modifications[node_name])
            if self.verbosity > 1:
                print "\tCheck in '%s' ..." % xml_file

            config = XMLFile.open(xml_file, "w")

            # Load the XML tree of the node content
            node_ref = "_xml_%s" % node_name.replace("-", "_")
            node_xml = getattr(self, node_ref)
            doc_plugin = xml.dom.minidom.parseString(node_xml)
            node = doc_plugin.getElementsByTagName(node_name).item(0)

            # Try to find and remove the node
            same_nodes = list()
            if self.verbosity > 2:
                print "\t\tSearch candidate node named '%s' for removal ..." \
                  % node_name
            candidates = config.get_document().getElementsByTagName(node_name)
            for candidate in candidates:
                if self.verbosity > 2:
                    print "\t\tFound a new candidate ..."
                for attr in candidate.attributes.keys():
                    if node.hasAttribute(attr) and \
                       candidate.getAttribute(attr) == node.getAttribute(attr):
                        continue
                    else:
                        break
                else:
                    same_nodes.append(candidate)
                    if self.verbosity > 12:
                        print "\t\tThe candidate is an old plugin node!"
            for candidate in same_nodes:
                if self.verbosity > 2:
                    print "\t\tRemove old plugin node ..."
                candidate.parentNode.removeChild(candidate)
                candidate.unlink()
            if not config.get_document().hasChildNodes():
                if self.verbosity > 2:
                    print "\t\t'%s' is now empty ..." % xml_file
            if not simulate_only: # Write the modifications
                config.write()

        if hasattr(self, "_report_defs") and hasattr(self, "_report_graph"):
            # Remove report and graph plugin definition
            graph_file = "%s/snmp-graph.properties" % self._path
            if self.verbosity > 1:
                print "\tCheck in '%s' ..." % graph_file
            line_is_rep_dec = False
            delete_next_line = False
            for line in fileinput.input(graph_file, inplace=1):
                # In the first part of the file are declared the graph's names
                # We have to look in this for any mention of self._report_defs
                line_is_rep_dec = self._is_part_of_report(line, line_is_rep_dec)
                if line_is_rep_dec:
                    for report_plugin_variable in self._report_defs:
                        if not simulate_only:
                            line = re.sub(r"%s,?\s*" % report_plugin_variable,
                                          "", line)
                    if re.match(r"\s*\\?\n", line) is None:
                        sys.stdout.write(line)
                    continue
                # In the remaning part are the graph's definition
                # We have to look and see if some match self._report_graph
                graph_property_found = False
                # Look if the line is the first of a graph definition
                for report_plugin_variable in self._report_defs:
                    p = r"\s*report\.%s\.\w+=.*\\?\n" % report_plugin_variable
                    graph_property_found |= bool(re.match(p, line))
                if not graph_property_found and not delete_next_line:
                    # If the line, nor the last one are, graph definitions
                    sys.stdout.write(line)
                else:
                    if simulate_only:
                        sys.stdout.write(line)
                    # Look if the line is a continuation of a graph definition
                    graph_continuity = bool(re.match(r".*\\\n", line))
                    delete_next_line = True if graph_continuity else False
            # Remove any double whiteline
            line_is_whiteline = False
            for line in fileinput.input(graph_file, inplace=1):
                previous_line_was_whiteline = line_is_whiteline
                line_is_whiteline = bool(re.match(r"\s*\n", line))
                if previous_line_was_whiteline and line_is_whiteline:
                    continue
                else:
                    sys.stdout.write(line)

    def get_verbosity(self):
        return self._verbosity
    def set_verbosity(self, verbosity):
        self._verbosity = verbosity
    verbosity = property(get_verbosity, set_verbosity)