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

from __future__ import with_statement

# Standard library
import fileinput
import optparse
import os
import re
import sys
import xml.dom.minidom

import params
import lib.distrib
from lib.ip import IP
from lib.xmlfile import XMLFile

try:
    # Python version >= 2.5
    import hashlib as md5
except:
    import md5

# This file need the ternary operator from Python 2.5.0
assert sys.version_info[:3] >= (2, 5, 0)

def add_to_admins(filename, username):
    """
    Add username to the users' list granted by admin roles defined in filename
    where filename is usualy "/etc/opennms/magic-users.properties".
    """
    role = "role.admin.users"
    for line in fileinput.input(filename, inplace = 1):
        if line[:len(role)] == role:
            admins = line[len(role)+1:len(line)-1].replace(" ", "").split(",")
            if not username in admins:
                admins.append(username)
                line = "%s=%s\n" % (role, ", ".join(admins))
        sys.stdout.write(line)


class XMLConfig(object):
    def __init__(self, xml_file, root_name = None):
        self._xml_file = xml_file
        self.xml_tree = XMLFile.open(xml_file, "w")
        self.xml_tree.set_root(root_name)
        self._doc = self.xml_tree.get_document()
        # root_conf is usualy the real root but not always.
        # root_conf's tag name is the same as filename
        root_conf = self._doc.getElementsByTagName(root_name)
        assert root_conf.length == 1
        self._config = root_conf.item(0)

    def get_overwrite(self):
        return self._overwrite
    def set_overwrite(self, overwrite):
        self._overwrite = overwrite
    overwrite = property(get_overwrite, set_overwrite)

    def get_verbosity(self):
        return self._verbosity
    def set_verbosity(self, verbosity):
        self._verbosity = verbosity
    verbosity = property(get_verbosity, set_verbosity)

    def save(self):
        self.xml_tree.write()

    def pretty_print(self):
        print "Printing '%s' with modifications made to it ..." % self._xml_file
        print "#" * 80
        print
        print self.xml_tree.read()
        print "#" * 80

    def remove_all(self):
        while self._config.firstChild is not None:
            self._config.removeChild(self._config.firstChild)
    def clean(self):
        self._doc.normalize()


class Users(XMLConfig):
    def add(self, uid, pwd, name=None, mail=None, ro=False):
        if self.verbosity > 1:
            print "\tAdding user '%s' ..." % uid
        # Create node
        new_user = self._doc.createElement("user")
        # Configure id
        user_id = self._doc.createElement("user-id")
        user_id.appendChild(self._doc.createTextNode(uid))
        new_user.appendChild(user_id)
        # Configure password
        password = self._doc.createElement("password")
        if pwd[:5] == "(md5)":
            # If password is already hashed, remove header and use the hash
            md5_pwd = pwd[5:]
        else:
            # Otherwize, compute the hash and use it
            md5_pwd = md5.md5(pwd).hexdigest().upper()
        password.appendChild(self._doc.createTextNode(md5_pwd))
        new_user.appendChild(password)
        # Configure full_name
        if name:
            full_name = self._doc.createElement("full-name")
            full_name.appendChild(self._doc.createTextNode(name))
            new_user.appendChild(full_name)
        # Configure email
        if mail:
            contact = self._doc.createElement("contact")
            contact.setAttribute("info", mail)
            contact.setAttribute("type", "email")
            new_user.appendChild(contact)
        # Configure permissions
        if ro:
            new_user.setAttribute("read-only", "true")
        # Search for all users and user-ids
        users = self._doc.getElementsByTagName("users").item(0)

        e_uids = self._doc.getElementsByTagName("user-id")
        # If a node have the same user-id, replace it
        old_users_matching = [e_uid.parentNode for e_uid in e_uids
                              if e_uid.firstChild.nodeValue == uid]
        if old_users_matching:
            assert len(old_users_matching) == 1
            if self.overwrite:
                users.replaceChild(new_user, old_users_matching[0])
            else:
                if self.verbosity > 1:
                    print "\t\tUser '%s' already exist but will not be " \
                          "overwritten!" % uid
        else: # Otherwise, add the node
            users.appendChild(new_user)


class Groups(XMLConfig):
    def add(self, name, comments = "", users = None, level = 2):
        if users is None:
            users = []
        if self.verbosity > 1:
            print "\tAdding group '%s' ..." % name
        # Search in all groups if one have the same name
        g_names = self._doc.getElementsByTagName("name")
        # If so, merge it
        old_groups_matching = [g_name.parentNode for g_name in g_names
                               if g_name.firstChild.nodeValue == name]
        if old_groups_matching:
            assert len(old_groups_matching) == 1
            new_group = old_groups_matching[0]
        else:
            new_group = self._doc.createElement("group")
            groups = self._doc.getElementsByTagName("groups").item(0)
            groups.appendChild(new_group)
            # Configure name
            group_name = self._doc.createElement("name")
            group_name.appendChild(self._doc.createTextNode(name))
            new_group.appendChild(group_name)
        # Configure comments
        for group_comments in new_group.getElementsByTagName("comments"):
            new_group.removeChild(group_comments)
        group_comments = self._doc.createElement("comments")
        group_comments.appendChild(self._doc.createTextNode(comments))
        new_group.appendChild(group_comments)
        # Configure users
        for old_user in new_group.getElementsByTagName("user"):
            new_group.removeChild(old_user)
        for user in users:
            new_user = self._doc.createElement("user")
            new_user.appendChild(self._doc.createTextNode(user))
            new_group.appendChild(new_user)
            # If the group is admin
            if level == 3:
                if self.verbosity > 1:
                    print "\tAdding user '%s' to admins ..." % user
                admin_conf = "%s/magic-users.properties" \
                             % os.path.dirname(self._xml_file)
                add_to_admins(admin_conf, user)


class Roles(XMLConfig):
    def add(self, name, group, supervisor, description=""):
        if self.verbosity > 1:
            print "\tAdding role '%s' ..." % name
        # Create role
        new_role = self._doc.createElement("role")
        new_role.setAttribute("name", name)
        new_role.setAttribute("membership-group", group)
        new_role.setAttribute("supervisor", supervisor)
        new_role.setAttribute("description", description)
        # Get roles or create it if it doesn't exist
        roles = self._doc.getElementsByTagName("roles").item(0)
        if roles is None:
            groupinfo = self._doc.getElementsByTagName("groupinfo").item(0)
            roles = self._doc.createElement("roles")
            groupinfo.appendChild(roles)
        else:
            # Remove role with the same name if exist
            #for role in roles.childNodes:
            for role in self._doc.getElementsByTagName("role"):
                if role.getAttribute("name") == name:
                    try:
                        roles.removeChild(role)
                    except xml.dom.NotFoundErr:
                        # Dont complain if we try to remove more than once
                        # the new range
                        pass

        # Add the new role
        roles.appendChild(new_role)


class Discovery(XMLConfig):
    """
    This class allow to manage the list of IPv4 address monitored by OpenNMS.
    """

    def add(self, addr, retries=1, timeout=2000):
        """
        Add an IPv4 address in dot-decimal notation.
        """
        if self.verbosity > 1:
            print "\tAdding '%s' ..." % addr
        # Create specific address
        new_address = self._doc.createElement("specific")
        new_address.appendChild(self._doc.createTextNode(addr))
        # Configure attributes
        new_address.setAttribute("retries", str(retries))
        new_address.setAttribute("timeout", str(timeout))
        # Search for all IP addresses
        discovery_configuration = \
            self._doc.getElementsByTagName("discovery-configuration").item(0)
        addresses = self._doc.getElementsByTagName("specific")
        old_addresses_matching = [address for address in addresses
                                  if address.firstChild.nodeValue == addr]
        # If the address is already configured, replace it
        if old_addresses_matching:
            assert len(old_addresses_matching) == 1
            discovery_configuration.replaceChild(new_address,
                                                 old_addresses_matching[0])
        else: # Otherwise, add the address
            discovery_configuration.appendChild(new_address)

    def manage_range(self, action, begin, end, retries=None, timeout=None):
        """
        Include or exclude an IPv4 address range in dot-decimal notation.
        """
        if self.verbosity > 1:
            print "\t%sing range from '%s' to '%s' ..." \
                  % (action.title()[:len(action)-1], begin, end)
        # Create range
        new_range = self._doc.createElement("%s-range" % action)
        # Configure border
        for border in ["begin", "end"]:
            range_border = self._doc.createElement(border)
            range_border.appendChild(self._doc.createTextNode(locals()[border]))
            new_range.appendChild(range_border)
        # Configure attributes
        if retries is not None:
            new_range.setAttribute("retries", str(retries))
        if timeout is not None:
            new_range.setAttribute("timeout", str(timeout))
        # Add the new range
        discovery_configuration = \
            self._doc.getElementsByTagName("discovery-configuration").item(0)
        discovery_configuration.appendChild(new_range)
        # Search in all ranges
        for range in self._doc.getElementsByTagName("%s-range" % action):
            range_begin = range.getElementsByTagName("begin").item(0)\
                .firstChild.nodeValue
            range_end = range.getElementsByTagName("end").item(0)\
                .firstChild.nodeValue
            # If the new range extend some old ranges, remove them
            if IP(begin) <= IP(range_begin) and IP(end) >= IP(range_end) and \
               not new_range.isSameNode(range):
                   discovery_configuration.removeChild(range)
            # BTW check if the new range is useless, and if so remove it
            elif IP(begin) >= IP(range_begin) and IP(end) <= IP(range_end) and \
                 not new_range.isSameNode(range):
                     try:
                         discovery_configuration.removeChild(new_range)
                     except xml.dom.NotFoundErr:
                         # Dont complain if we try to remove more than once
                         # the new range
                         pass

    def include(self, begin, end, retries = 1, timeout = 2000):
        self.manage_range("include", begin, end, retries, timeout)

    def exclude(self, begin, end):
        self.manage_range("exclude", begin, end)


class Notification(XMLConfig):
    """
    This class allow checking the status of the OpenNMS notification daemon.
    """
    def get_status(self):
        notifd = self._doc.getElementsByTagName("notifd-configuration").item(0)
        return True if notifd.getAttribute("status") == "on" else False
    def set_status(self, value):
        notifd = self._doc.getElementsByTagName("notifd-configuration").item(0)
        status = "on" if value else "off"
        if self.verbosity > 1:
            print "\tSetting notification status to '%s' ..." % status
        notifd.setAttribute("status", status)
    status = property(get_status, set_status)


class Collector(XMLConfig):
    """
    This class allow checking the status of SNMP and WMI protocols used by
    OpenNMS to collect informations about the network.
    """
    def get_protocol_status(self, protocol):
        """ Generic method to get the status of the given protocol """
        assert self._doc.getElementsByTagName("package").length == 1
        for service in self._doc.getElementsByTagName("service"):
            if service.getAttribute("name") != protocol:
                continue
            return True if service.getAttribute("status") == "on" else False
    def set_protocol_status(self, protocol, value):
        """ Generic method to set the status of the given protocol """
        assert self._doc.getElementsByTagName("package").length == 1
        for service in self._doc.getElementsByTagName("service"):
            if service.getAttribute("name") != protocol:
                continue
            status = "on" if value else "off"
            if self.verbosity > 1:
                print "\tSetting %s status to '%s' ..." % (protocol, status)
            service.setAttribute("status", status)

    """ SNMP getters and setters """
    def get_snmp(self):
        self.get_protocol_status("SNMP")
    def set_snmp(self, value):
        self.set_protocol_status("SNMP", value)
    snmp = property(get_snmp, set_snmp)

    """ WMI getters and setters """
    def get_wmi(self):
        self.get_protocol_status("WMI")
    def set_wmi(self, value):
        self.set_protocol_status("WMI", value)
    wmi = property(get_wmi, set_wmi)


class Credentials(XMLConfig):
    """
    This class allow to define credential for for an address or a range of
    addresses for the SNMP or WMI protocol.
    """

    def _add_specific(self, node, value):
        child = self._doc.createElement("specific")
        child.appendChild(self._doc.createTextNode(str(value)))
        node.appendChild(child)
        return child

    def _add_range(self, node, left_value, right_value):
        child = self._doc.createElement("range")
        child.setAttribute("begin", str(left_value))
        child.setAttribute("end", str(right_value))
        node.appendChild(child)
        return child

    def create_element(self, protocol, begin = None, end = None, **credential):
        """ Define a creditential and add it to the configuration """
        element = None
        if begin is None:
            # Add default credential
            element = self._config
        else:
            # Firs we need some lambda expressions ...
            # Become true if 'dic' and 'elt' have the same 'key'
            have_same_attr = lambda dic, elt, key: \
                key in dic and \
                elt.hasAttribute(key) and \
                dic[key] == elt.getAttribute(key)
            # Become true if 'dic' and 'elt' don't have 'key'
            dont_have_attr = lambda dic, elt, key: \
                key not in dic and \
                not elt.hasAttribute(key)
            # Become true if 'dic' and 'elt' have the same child text
            have_same_spec = lambda dic, elt: \
                "begin" in dic and \
                elt.hasAttribute(key) and \
                dic[key] == elt.getAttribute(key)
            # Search if we can reuse a previous definition ...
            for old_def in self._doc.getElementsByTagName("definition"):
                if have_same_attr(credential, old_def, "read-community") and \
                    (
                        have_same_attr(credential, old_def, "version") or \
                        dont_have_attr(credential, old_def, "version")
                    ):
                        # Reuse a SNMP definition
                        element = old_def
                elif have_same_attr(credential, old_def, "username") and \
                     have_same_attr(credential, old_def, "domain"):
                        # Reuse a WMI definition
                        element = old_def
                else:
                    continue # the search for a reusable previous definition
                # Quick check to see if we really need this entry
                for old_range in element.getElementsByTagName("range"):
                    old_lip = IP(old_range.getAttribute("begin"))
                    old_rip = IP(old_range.getAttribute("end"))
                    new_ip = IP(begin)
                    assert old_lip < old_rip
                    if end is not None:
                        assert IP(begin) < IP(end)
                    if old_lip <= new_ip and new_ip <= old_rip:
                        warn_msg = lambda new, old: \
                            "\tWarning: '%s' is in '%s', skipped!" % (new, old)
                        # If begin is within an old range
                        if end is None:
                            # If it's a specific, then it is useless
                            if self.verbosity > 1:
                                print warn_msg(new_ip,
                                               "%s-%s" % (old_lip, old_rip))
                            return # We could stop here
                        elif old_lip <= IP(end) and IP(end) <= old_rip:
                            # If end is within the range too, then it's useless
                            if self.verbosity > 1:
                                print warn_msg("%s-%s" % (new_ip, IP(end)),
                                               "%s-%s" % (old_lip, old_rip))
                            return # We could stop here
                    """
                    #TODO: This introduce some bugs...
                        elif old_rip <= IP(end):
                            # Extend the right border of the old range
                            old_range.setAttribute("end", end)
                            return # We could stop here
                    elif new_ip <= old_lip and end is not None:
                        # If begin is at the left of the old range
                        if old_lip <= IP(end) and IP(end) <= old_rip:
                            # But end is within the range, then extend the left
                            # border of the old range
                            old_range.setAttribute("begin", begin)
                            return # We could stop here
                    """
                break # No need to create a new definition, skip 'else'
            else: # If we did not found any reusable definition
                element = self._doc.createElement("definition")
                self._config.appendChild(element)
            # Search if we have to change some old ranges
            for old_range in self._doc.getElementsByTagName("range"):
                old_lip = IP(old_range.getAttribute("begin"))
                old_rip = IP(old_range.getAttribute("end"))
                new_lip = IP(begin)
                new_rip = IP(end)
                old_def = old_range.parentNode
                # If old range borders are touching, create a new specific
                if old_lip == old_rip:
                    self._add_specific(old_def, old_lip)
                # If the given ip or new range left border is in the old range
                elif (old_lip <= new_lip and new_lip <= old_rip) or \
                     (end is not None and new_lip <= old_lip and \
                      old_lip <= new_rip):
                    # And if there is room for a new left range, create it
                    if old_lip < new_lip - 1:
                        self._add_range(old_def, old_lip, (new_lip - 1))
                    # Otherwise create a new ip for the old left border
                    elif old_lip == new_lip - 1:
                        self._add_specific(old_def, old_lip)
                    # If we are adding a new ip
                    if end is None:
                        # And if there is room for a new right range, create it
                        if new_lip + 1 < old_rip:
                            self._add_range(old_def, new_lip + 1, old_rip)
                        # Otherwise create a new ip for the old right border
                        else:
                            self._add_specific(old_def, old_rip)
                    # If we are adding a new range
                    else:
                        # And if there is room for a new right range, create it
                        if new_rip + 1 < old_rip:
                            self._add_range(old_def, new_rip + 1, old_rip)
                        # Otherwise if there is room for just a ip
                        elif new_rip + 1 == old_rip:
                            # create it for the old right border
                            self._add_specific(old_def, old_rip)
                else:
                    # If we dont have changed the old range, stop here
                    continue
                # Otherwise remove it
                old_def.removeChild(old_range)
            # Search if we could remove some old specific
            for old_spec in self._doc.getElementsByTagName("specific"):
                old_ip = IP(old_spec.firstChild.nodeValue)
                new_ip = IP(begin)
                old_def = old_spec.parentNode
                if old_ip == new_ip:
                    old_def.removeChild(old_spec)
                    # Search if we could remove some empty definitions
                for old_def in self._doc.getElementsByTagName("definition"):
                    if not old_def.isSameNode(element):
                        for child in old_def.childNodes:
                            if child.nodeType is xml.dom.Node.ELEMENT_NODE:
                                break
                        else:
                            self._config.removeChild(old_def)
            child_element = None
            if end is None:
                # Add specific IP address
                child_element = self._doc.createElement("specific")
                child_element.appendChild(self._doc.createTextNode(begin))
            else:
                # Add range of IP addresses
                child_element = self._doc.createElement("range")
                for attr in ["begin", "end"]:
                    child_element.setAttribute(attr, locals()[attr])
            element.appendChild(child_element)
        # Add or replace credential attributes
        for attr in credential:
            if element.hasAttribute(attr):
                element.removeAttribute(attr)
            element.setAttribute(attr, credential[attr])

    def add(self, **args):
        """ Add SNMP or WMI creditentials """
        proto = None
        msg = lambda p, t, n: "\tAdding %s credential for %s '%s'" % (p, t, n)
        if "username" in args and "domain" in args: # WMI
            if self.verbosity > 1:
                print msg("WMI", "user",
                          "%s/%s" % (args["username"], args["domain"])),
            proto = "wmi"
        elif "username" not in args and "domain" not in args: # SNMP
            if "community" in args:
                if self.verbosity > 1:
                    print msg("SNMP", "community", args["community"]),
                args["read-community"] = args["community"]
                del args["community"]
                proto = "snmp"
        if "begin" not in args:
            if self.verbosity > 1:
                print "as the default credential ..."
        elif "end" not in args:
            if self.verbosity > 1:
                print "for '%s' ..." % args["begin"]
        else:
            if self.verbosity > 1:
                print "for '%s' to '%s' ..." % (args["begin"], args["end"])
        self.create_element(proto, **args)


class SnmpCredentials(Credentials):
    """ Trivial wrapper class for the SNMP protocol """


class WmiCredentials(Credentials):
    """ Trivial wrapper class for the WMI protocol """


class Capabilities(XMLConfig):
    """
    This class allow to define credential for for an address or a range of
    addresses for the SNMP or WMI protocol.
    """

    def _add_property(self, plugin, key, value):
        """
        Internal method
        Add a element named 'property' to the given 'plugin' element with two
        attributes: 'key' and 'value'.
        """
        prop = self._doc.createElement("property")
        prop.setAttribute("key", key)
        prop.setAttribute("value", value)
        plugin.appendChild(prop)

    def add_wmi(self):
        """ Add WMI protocol to the discovery daemon Capsd """
        if self.verbosity > 1:
            print "\tAdding WMI discovery capacibility ..."
        """
        root = self._doc.getElementsByTagName("capsd-configuration")
        assert root.length == 1
        config = root.item(0)
        """
        # Remove all hypothetical old entries
        for old_plugin in self._doc.getElementsByTagName("protocol-plugin"):
            if old_plugin.getAttribute("protocol") == "WMI":
                self._config.removeChild(old_plugin)
        plugin = self._doc.createElement("protocol-plugin")
        self._config.appendChild(plugin)
        plugin.setAttribute("protocol", "WMI")
        plugin.setAttribute("class-name",
                            "org.opennms.netmgt.capsd.plugins.WmiPlugin")
        plugin.setAttribute("scan", "on")
        plugin.setAttribute("user-defined", "false")
        prop = lambda k, v: self._add_property(plugin, k, v)
        prop("timeout", "2000")
        prop("retry", "1")
        prop("matchType", "all")
        prop("wmiClass", "Win32_ComputerSystem")
        prop("wmiObject", "Status")
        prop("compareOp", "EQ")
        prop("compareValue", "OK")
        prop("service-name", "WMI")

class Authentification(XMLConfig):

    def duplicate_role(self, old, new):
        """
        Add new role everywhere old role is defined.
        """
        assert old != new
        for url in self._doc.getElementsByTagName("intercept-url"):
            access = url.getAttribute("access")
            if not new in access.split(",") and old in access.split(","):
                url.setAttribute("access", "%s,%s" % (access, new))

    def _remove_previous_bean(self, attr):
        """
        Remote any previous LDAP configuration.
        """
        for bean in self._doc.getElementsByTagName("beans:bean"):
            if bean.getAttribute("id") == attr:
                bean.parentNode.removeChild(bean)

    def _add_bean(self, attr_id, attr_class):
        """
        Add a bean to the configuration and return it.
        """
        self._remove_previous_bean(attr_id)
        bean = self._doc.createElement("beans:bean")
        self._config.appendChild(bean)
        bean.setAttribute("id", attr_id)
        bean.setAttribute("class", attr_class)
        return bean

    def enable_ldap(self, address, port, domain, search_user, search_password,
                    user_filter, role_filter, auth_filter, default_role):
        """
        Enable LDAP authentification with the following parameters:
            address:            LDAP server's address
            port:               LDAP server's port
            domain:             LDAP Domain (ex: dc=example,dc=com)
            search_user:        Username executing the query
            search_password:    Password for this username
            user_filter:        Limit the user's search on a subtree
            role_filter:        Limit the role's search on a subtree
            auth_filter:        Attribute used to perform authentification
            default_role:       Default role given to LDAP users
        """

        sping = "org.springframework.security."

        context_source = self._add_bean(
            "contextSource",
            sping + "ldap.DefaultSpringSecurityContextSource")
        cons = self._doc.createElement("beans:constructor-arg")
        context_source.appendChild(cons)
        cons.setAttribute("value", "ldap://%s:%s/%s" % (address, port, domain))
        prop = self._doc.createElement("beans:property")
        context_source.appendChild(prop)
        prop.setAttribute("name", "userDn")
        prop.setAttribute("value", search_user)
        prop = self._doc.createElement("beans:property")
        context_source.appendChild(prop)
        prop.setAttribute("name", "password")
        prop.setAttribute("value", search_password)

        ldap_auth_provider = self._add_bean(
            "ldapAuthProvider",
            sping + "providers.ldap.LdapAuthenticationProvider")
        cust = self._doc.createElement("custom-authentication-provider")
        ldap_auth_provider.appendChild(cust)
        cons = self._doc.createElement("beans:constructor-arg")
        ldap_auth_provider.appendChild(cons)
        cons.setAttribute("ref", "ldapAuthenticator")
        cons = self._doc.createElement("beans:constructor-arg")
        ldap_auth_provider.appendChild(cons)
        cons.setAttribute("ref", "ldapAuthoritiesPopulator")

        ldap_auth = self._add_bean(
            "ldapAuthenticator",
            sping + "providers.ldap.authenticator.BindAuthenticator")
        cons = self._doc.createElement("beans:constructor-arg")
        ldap_auth.appendChild(cons)
        cons.setAttribute("ref", "contextSource")
        prop = self._doc.createElement("beans:property")
        ldap_auth.appendChild(prop)
        prop.setAttribute("name", "userSearch")
        prop.setAttribute("ref", "userSearch")

        user_search = self._add_bean(
            "userSearch",
            sping + "ldap.search.FilterBasedLdapUserSearch")
        cons = self._doc.createElement("beans:constructor-arg")
        user_search.appendChild(cons)
        cons.setAttribute("index", "0")
        cons.setAttribute("value", user_filter)
        cons = self._doc.createElement("beans:constructor-arg")
        user_search.appendChild(cons)
        cons.setAttribute("index", "1")
        cons.setAttribute("value", "(%s={0})" % auth_filter)
        cons = self._doc.createElement("beans:constructor-arg")
        user_search.appendChild(cons)
        cons.setAttribute("index","2" )
        cons.setAttribute("ref", "contextSource")
        prop = self._doc.createElement("beans:property")
        user_search.appendChild(prop)
        prop.setAttribute("name", "searchSubtree")
        prop.setAttribute("value", "true")

        ldap_auth_populator = self._add_bean(
            "ldapAuthoritiesPopulator",
            sping + "ldap.populator.DefaultLdapAuthoritiesPopulator")
        cons = self._doc.createElement("beans:constructor-arg")
        ldap_auth_populator.appendChild(cons)
        cons.setAttribute("ref", "contextSource")
        cons = self._doc.createElement("beans:constructor-arg")
        ldap_auth_populator.appendChild(cons)
        cons.setAttribute("value", role_filter)
        prop = self._doc.createElement("beans:property")
        ldap_auth_populator.appendChild(prop)
        prop.setAttribute("name", "groupRoleAttribute")
        prop.setAttribute("value", "cn")
        prop = self._doc.createElement("beans:property")
        ldap_auth_populator.appendChild(prop)
        prop.setAttribute("name", "groupSearchFilter")
        prop.setAttribute("value", "(member={0})")
        prop = self._doc.createElement("beans:property")
        ldap_auth_populator.appendChild(prop)
        prop.setAttribute("name", "searchSubtree")
        prop.setAttribute("value", "true")
        prop = self._doc.createElement("beans:property")
        ldap_auth_populator.appendChild(prop)
        prop.setAttribute("name", "rolePrefix")
        prop.setAttribute("value", "")
        prop = self._doc.createElement("beans:property")
        ldap_auth_populator.appendChild(prop)
        prop.setAttribute("name", "convertToUpperCase")
        prop.setAttribute("value", "true")
        prop = self._doc.createElement("beans:property")
        ldap_auth_populator.appendChild(prop)
        prop.setAttribute("name", "defaultRole")
        prop.setAttribute("value", default_role)

class Mail(XMLConfig):
    def add(self, name, server, address, username, password):
        """
        Configure JavaMail with the following parameters:
            name:       name given to this configuration
            server:     mail server's address or name (SMTP+POP3 at the time)
            address:    OpenNMS mail account's address
            username:   OpenNMS mail account's username
            password:   OpenNMS mail account's password
        """
        # TODO: add parameters to allow a more flexible configuration

        if self.verbosity > 1:
            print "\tConfiguring Mail ..."

        self._doc.firstChild.setAttribute("default-read-config-name", name)
        self._doc.firstChild.setAttribute("default-send-config-name", name)

        for config in self._doc.getElementsByTagName("sendmail-config"):
            if config.getAttribute("name") == name:
                self._config.removeChild(config)
        sendmail_config = self._doc.createElement("sendmail-config")
        self._config.appendChild(sendmail_config)
        sendmail_config.setAttribute("name", name)
        sendmail_config.setAttribute("attempt-interval", "3000")
        sendmail_config.setAttribute("use-authentication", "false")
        sendmail_config.setAttribute("use-jmta", "false")
        sendmail_config.setAttribute("debug", "false")

        sendmail_host = self._doc.createElement("sendmail-host")
        sendmail_config.appendChild(sendmail_host)
        sendmail_host.setAttribute("host", server)
        sendmail_host.setAttribute("port", "25")

        sendmail_protocol = self._doc.createElement("sendmail-protocol")
        sendmail_config.appendChild(sendmail_protocol)
        sendmail_protocol.setAttribute("char-set", "utf-8")
        sendmail_protocol.setAttribute("mailer", "smtpsend")
        sendmail_protocol.setAttribute("message-content-type", "text/plain")
        sendmail_protocol.setAttribute("message-encoding", "7-bit")
        sendmail_protocol.setAttribute("quit-wait", "true")
        sendmail_protocol.setAttribute("ssl-enable", "false")
        sendmail_protocol.setAttribute("start-tls", "false")
        sendmail_protocol.setAttribute("transport", "smtp")
                     
        sendmail_message = self._doc.createElement("sendmail-message")
        sendmail_config.appendChild(sendmail_message)
        sendmail_message.setAttribute("to", "user@example.org")
        sendmail_message.setAttribute("from", "user@example.org")
        sendmail_message.setAttribute("subject", "OpenNMS Test Message")
        sendmail_message.setAttribute("body", "This is an OpenNMS test message.")

        user_auth = self._doc.createElement("user-auth")
        sendmail_config.appendChild(user_auth)
        user_auth.setAttribute("user-name", username)
        user_auth.setAttribute("password", password)

        for config in self._doc.getElementsByTagName("readmail-config"):
            if config.getAttribute("name") == name:
                self._config.removeChild(config)
        readmail_config = self._doc.createElement("readmail-config")
        self._config.appendChild(readmail_config)
        readmail_config.setAttribute("name", name)
        readmail_config.setAttribute("attempt-interval", "1000")
        readmail_config.setAttribute("delete-all-mail", "false")
        readmail_config.setAttribute("mail-folder", "INBOX")
        readmail_config.setAttribute("debug", "true")

        javamail_property = self._doc.createElement("javamail-property")
        readmail_config.appendChild(javamail_property)
        javamail_property.setAttribute("name", "mail.pop3.apop.enable")
        javamail_property.setAttribute("value", "false")

        javamail_property = self._doc.createElement("javamail-property")
        readmail_config.appendChild(javamail_property)
        javamail_property.setAttribute("name", "mail.pop3.rsetbeforequit")
        javamail_property.setAttribute("value", "false")

        readmail_host = self._doc.createElement("readmail-host")
        readmail_config.appendChild(readmail_host)
        readmail_host.setAttribute("host", server)
        readmail_host.setAttribute("port", "143")

        readmail_protocol = self._doc.createElement("readmail-protocol")
        readmail_host.appendChild(readmail_protocol)
        readmail_protocol.setAttribute("ssl-enable", "false")
        readmail_protocol.setAttribute("start-tls", "false")
        readmail_protocol.setAttribute("transport", "pop3")

        user_auth = self._doc.createElement("user-auth")
        readmail_config.appendChild(user_auth)
        user_auth.setAttribute("user-name", username)
        user_auth.setAttribute("password", password)
        
        for config in self._doc.getElementsByTagName("end2end-mail-config"):
            self._config.removeChild(config)
        end2end_mail_config = self._doc.createElement("end2end-mail-config")
        self._config.appendChild(end2end_mail_config)
        end2end_mail_config.setAttribute("readmail-config-name", name)
        end2end_mail_config.setAttribute("sendmail-config-name", name)
        end2end_mail_config.setAttribute("name", "default")

        admin_conf = "%s/javamail-configuration.properties" \
                     % os.path.dirname(self._xml_file)
        if self.verbosity > 1:
            print "\tConfiguring .properties file ..."       
        with open(admin_conf, 'w') as f:
            f.write("org.opennms.core.utils.fromAddress=%s\n" % address)
            f.write("org.opennms.core.utils.mailHost=%s\n" % server)
            f.write("org.opennms.core.utils.useJMTA=false\n")
            f.write("org.opennms.core.utils.authenticate=false\n")
            f.write("org.opennms.core.utils.messageContentType=text/plain\n")
            f.write("org.opennms.core.utils.charset=utf-8\n")
        f.close()
        
##########################################
#             Main Function              #
##########################################

def main():

    ##########################################
    #            Parse arguments             #
    ##########################################

    parser = optparse.OptionParser(usage="%prog [options]",
    version="%prog 0.1.1")
    parser.add_option("-v", "--verbose", \
        help="Increase verbosity level (use twice or more for greater effect)",
        action = "count",
        default = 0,
        dest = "verbosity")
    parser.add_option("-c", "--configuration-path", \
        help = "If OpenNMS's configuration path is not '%s', fix it to the " \
               "given path.",
        metavar = "<path>",
        default = params.opennms_config_path)
    parser.add_option("-f", "--configuration-file", \
        help = "If 'config_rules.py' is not in the script's directory but at " \
               "the given location.",
        metavar = "<path>",
        default = ".")
    parser.add_option("--save", \
        help = "Append 'config_rules.py' to OpenNMS configuration",
        action="store_true")
    parser.add_option("--remove", \
        help = "Remove 'config_rules.py' from OpenNMS configuration",
        action="store_true")
    parser.add_option("-p", "--print", \
        help = "Preview modifications of OpenNMS configuration",
        action = "store_true",
        dest = "pretty_print")


    (options, args) = parser.parse_args()

    # Check if we've got a valid configuration directory
    if not os.path.isfile("%s/opennms.properties" % options.configuration_path):
        print >> sys.stderr, \
                 "'%s' doesn't contain OpenNMS's configuration files!\n" \
                 "Use '-c' to choose another directory.\n" \
                 % options.configuration_path
        rep = raw_input("Continue anyway? [y/N] ")
        if not re.match("^[yY]([eE][sS])?$", rep):
            sys.exit(os.EX_OK)

    if (options.save or options.remove) and os.geteuid():
        print >> sys.stderr, \
        "Error: you cannot perform this operation unless you are root."
        exit(os.EX_NOPERM)
    
    ##########################################
    #         Parse 'config_rules.py'        #
    ##########################################

    # Import user configuration defined in 'config_rules.py'
    import config_rules
    
    errors_detected = 0
    print_error = lambda l, n, t: "Error in %s: '%s' is not a valid %s!" \
                                  % (l, n, t)
    # Check if all users mentionned in GROUPS exist in USERS
    for uids in [group['users'] for group in config_rules.GROUPS if 'users'
                                                                     in group]:
        for uid in uids:
            if uid not in [user['uid'] for user in config_rules.USERS]:
                errors_detected += 1
                print >> sys.stderr, print_error("GROUPS", uid, "user")
    # Check if all groups mentionned in ROLES exist in GROUPS
    for name in [role['group'] for role in config_rules.ROLES if 'group'
                                                                      in role]:
        if name not in [group['name'] for group in config_rules.GROUPS]:
            errors_detected += 1
            print >> sys.stderr, print_error("ROLES", name, "group")
    # Check if all users mentionned in ROLES exist in USERS
    for uid in [role['supervisor'] for role in config_rules.ROLES
                                                      if 'supervisor' in role]:
        if uid not in [user['uid'] for user in config_rules.USERS]:
            errors_detected += 1
            print >> sys.stderr, print_error("ROLES", uid, "user")
    # Exit if errors detected
    if errors_detected:
        plural = "s"
        if errors_detected == 1:
            plural = ""
        sys.exit("%d error%s detected in 'config_rules.py'" % (errors_detected,
                                                                plural))

    # Define modifiable configuration files
    # each key.capitalize() of this map should have a class with the same name
    xml_config_files = {
        "users": "users.xml",
        "groups": "groups.xml",
        "roles": "groups.xml",
        "discovery": "discovery-configuration.xml",
        "notification": "notifd-configuration.xml",
        "collector": "collectd-configuration.xml",
        "capabilities": "capsd-configuration.xml",
        "snmp_credentials": "snmp-config.xml",
        "wmi_credentials": "wmi-config.xml",
        "authentification": "applicationContext-spring-security.xml",
        "mail": "javamail-configuration.xml",
    }

    is_def = lambda conf, var: hasattr(conf, str(var))
    ldap_vars = [
        "LDAP_ADDRESS", "LDAP_PORT", "LDAP_USERNAME", "LDAP_PASSWORD",
        "LDAP_USERS_KEYS", "LDAP_USERS_GROUP",
        "LDAP_USERS_PASSWORD", "LDAP_USERS_READ_ONLY",
        "LDAP_DOMAIN", "LDAP_FILTER_USER", "LDAP_FILTER_ROLE",
    ]    
    is_ldap_enabled = lambda c: not False in [is_def(c, v) for v in ldap_vars]
    mail_vars = [
        "MAIL_NAME", "MAIL_SERVER", "MAIL_ADDRESS", 
        "MAIL_USERNAME", "MAIL_PASSWORD"
    ]    
    is_mail_enabled = lambda c: not False in [is_def(c, v) for v in mail_vars]

    # Apply modifications listed in 'config_rules.py'
    print "#" * 80
    print "Loading modifications listed in 'config_rules.py' ..."
    for key in xml_config_files.keys():

        # Instanciate configuration object
        path = "%s/jetty-webapps/opennms/WEB-INF" % params.opennms_path \
            if key == "authentification" else options.configuration_path
        config_file = "%s/%s" % (path, xml_config_files[key])
        if options.verbosity > 0:
            print "Editing '%s' ..." % config_file
        root_name = "beans:beans" if key == "authentification" \
                            else xml_config_files[key].split(".")[0]
        config = globals()[key.title().replace("_", "")](config_file, root_name)
        config.verbosity = options.verbosity

        # Call its methods for specifics elements defined in 'config_rules.py'
        if key in ["users", "groups", "roles", "snmp_credentials",
                   "wmi_credentials", "mail"]:
            # TODO if groups or mail backup file.properties and restore it 
            # after if option save is not set. Remove the backup in the end.
            if hasattr(config_rules, "REMOVE_PREVIOUS_%s" % key.upper()):
                if getattr(config_rules, "REMOVE_PREVIOUS_%s" % key.upper()):
                    if options.verbosity > 2:
                        print "Removing all previous configuration ..."
                    config.remove_all()
            if hasattr(config_rules, "OVERWRITE_PREVIOUS_%s" % key.upper()) and \
               getattr(config_rules, "OVERWRITE_PREVIOUS_%s" % key.upper()):
                config.overwrite = True
            else:
                config.overwrite = False

            # Get LDAP USERS
            ldap_group = None
            ldap_group_users = list()
            if key in ("users", "groups") and is_ldap_enabled(config_rules):
                   try:
                       import ldap
                   except ImportError:
                       sys.exit("Error: You must have 'python-ldap' on your " \
                                "system!")
                   ldap_address = getattr(config_rules, "LDAP_ADDRESS")
                   ldap_port = getattr(config_rules, "LDAP_PORT")
                   ldap_username = getattr(config_rules, "LDAP_USERNAME")
                   ldap_password = getattr(config_rules, "LDAP_PASSWORD")
                   ldap_domain = getattr(config_rules, "LDAP_DOMAIN")
                   filter_user = getattr(config_rules, "LDAP_FILTER_USER")
                   items = getattr(config_rules, "LDAP_USERS_KEYS")
                   ldap_group = getattr(config_rules, "LDAP_USERS_GROUP")
                   uri = 'ldap://%s:%s' % (ldap_address, ldap_port)
                   l = ldap.initialize(uri)
                   l.bind(ldap_username, ldap_password)
                   r = l.search_s("%s,%s" % (filter_user, ldap_domain), 
                                  ldap.SCOPE_SUBTREE, '(objectClass=*)', 
                                  items.values())
                   l.unbind()
                   handle = lambda entry, k: \
                       entry[k][0] if k in entry and len(entry[k]) == 1 \
                       else None
                   for dn, entry in r:
                       elem = dict()
                       is_full_account = True
                       for k, v in items.items():
                           obj = handle(entry, v)
                           if obj is not None:
                               elem[k] = obj
                           else:
                               is_full_account = False
                       if is_full_account:
                           # If we've got all we need, create the user
                           if key == "users":
                               if options.verbosity > 1:
                                   print "\tFound LDAP user '%s' ..." \
                                         % elem['uid']
                               elem['pwd'] = getattr(config_rules,
                                                   "LDAP_USERS_PASSWORD")
                               elem['ro'] = getattr(config_rules,
                                                   "LDAP_USERS_READ_ONLY")
                               config.add(**elem)
                           elif key == "groups":
                               # Populate the ldap default group
                               ldap_group_users.append(elem['uid'])

            # Add elements to the XML configuration
            if hasattr(config_rules, key.upper()):
                for elem in getattr(config_rules, key.upper()):
                    if key == "groups" and ldap_group is not None and \
                       elem['name'] == ldap_group:
                           elem['users'].extend(ldap_group_users)
                    config.add(**elem)
            if key == "mail":
                name = getattr(config_rules, "MAIL_NAME")
                server = getattr(config_rules, "MAIL_SERVER")
                address = getattr(config_rules, "MAIL_ADDRESS")
                username = getattr(config_rules, "MAIL_USERNAME")
                password = getattr(config_rules, "MAIL_PASSWORD")
                config.add(name, server, address, username, password)

        elif key == "notification":
            config.status = getattr(config_rules, key.upper())
        elif key == "collector":
            for proto in ["snmp", "wmi"]:
                if hasattr(config_rules, proto.upper()):
                    setattr(config, proto, getattr(config_rules, proto.upper()))
        elif key == "capabilities":
            if hasattr(config_rules, "WMI") and getattr(config_rules, "WMI"):
                getattr(config, "add_wmi")()
        elif key == "discovery":
            for action in ["include_ranges", "exclude_ranges", "add_addresses"]:
                config_param = action.upper()
                if hasattr(config_rules, config_param):
                    for elem in getattr(config_rules, config_param):
                        getattr(config, action.split("_")[0])(**elem)
        elif key == "authentification" and is_ldap_enabled(config_rules):
            ldap_address = getattr(config_rules, "LDAP_ADDRESS")
            ldap_port = getattr(config_rules, "LDAP_PORT")
            ldap_username = getattr(config_rules, "LDAP_USERNAME")
            ldap_password = getattr(config_rules, "LDAP_PASSWORD")
            ldap_domain = getattr(config_rules, "LDAP_DOMAIN")
            filter_user = getattr(config_rules, "LDAP_FILTER_USER")
            filter_role = getattr(config_rules, "LDAP_FILTER_ROLE")
            ldap_group = getattr(config_rules, "LDAP_USERS_GROUP")
            items = getattr(config_rules, "LDAP_USERS_KEYS")
            # Find default role from default group
            if hasattr(config_rules, "GROUPS"):
                groups = getattr(config_rules, "GROUPS")
                levels = [group["level"] for group in groups
                          if "level" in group and group["name"] == ldap_group]
                role = "ROLE_USER"
                if len(levels) == 1 and int(levels[0]) == 3:
                    role = "ROLE_ADMIN"
                    # We can only assign one default role, but an admin need
                    # ROLE_ADMIN *and* ROLE_USER so we have to duplicate
                    # ROLE_USER permission to ROLE_ADMIN
                    config.duplicate_role("ROLE_USER", "ROLE_ADMIN")
            # Enable LDAP
            config.enable_ldap(ldap_address, ldap_port, ldap_domain,
                               ldap_username, ldap_password,
                               filter_user, filter_role,
                               items["uid"], role)

        # If asked to save or print the modifications
        for param in ["pretty_print", "save"]:
            if options.verbosity > 2:
                print "%s modifications to '%s' ..." \
                      % (param.capitalize(), config_file)
            if getattr(options, param):
                getattr(config, param)()

    if hasattr(config_rules, "PLUGINS"):
        print "#" * 80
        print "Adding plugins ..."
        for plugin_name in getattr(config_rules, "PLUGINS"):
            lib = "plugins.%s" % plugin_name
            __import__(lib)
            plugin = getattr(sys.modules[lib],
                        plugin_name.capitalize())(options.configuration_path)
            plugin.verbosity = options.verbosity
            if options.remove:
                plugin.disable(False)
            else:
                plugin.disable(not options.save)
                plugin.enable(not options.save)

    if hasattr(config_rules, "PROCESS_WIN32"):
        print "#" * 80
        print "Adding Win32 service monitoring ..."
        from plugins.win32 import Win32
        for p in getattr(config_rules, "PROCESS_WIN32"):
            process = Win32(options.configuration_path, p["name"], p["value"])
            process.verbosity = options.verbosity
            if options.remove:
                process.disable(False)
            else:
                process.disable(not options.save)
                process.enable(not options.save)
                print "... for service '%s'" % p["name"]
                
if __name__ == "__main__":

    main()
    sys.exit(os.EX_OK)
