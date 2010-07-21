# -*- coding: utf-8 -*-
################################################################################
# This present "configuration file" follow the Python syntax in order to define
# the changes "config.py" will have to make on the OpenNMS configuration.
#
# The aim of this script is to provide you a tool for defining your monitoring
# strategy and merge it immediatly with any existing installation (thus using
# a fresh install might be a good idea).
#
# You will have on one place a list of all users and groups and theirs roles on
# your organisation. You will also define the network and the creditentials
# required to monitor it with SNMP or WMI protocol. At last you will also
# have the possibility to activate any plugins defined in the plugins directory.
#
# WARNINGS: 
#   * Before running "config.py --save" you are strongly advised to use
#     "backup.py" to secure the present state of the configuration files and
#     the database.
#   * Before doing any modifications to a previous configuration it may be a
#     good idea to run  "config.py --remove", this is especialy true for
#     removing or modifing a plugin because "config.py" will have no way to
#     detect a previous version if his is different.
#   * One more time: "backup.py" and "restore.py" are easy so use them!
#

################################################################################
# Add a list of users to the default configuration
#
# A user is defined by the following parameters:
#   uid(*)        :   user-id
#   pwd(*)        :   password in plaintext or in hexadecimal MD5 with '(md5)' like this:
#                     'pwd': 'secret'
#                     'pwd': '(md5)5EBE2294ECD0E0F08EAB7690D2A6EE69'
#   name          :   full name
#   mail          :   email address
#   ro            :   read-only (True | False (default))
#
# Parameters not marqued by (*) are optionals
#
# Do not remove 'admin' user!
#
REMOVE_PREVIOUS_USERS = True
OVERWRITE_PREVIOUS_USERS = True
USERS = [
    {'uid': 'admin', 'pwd': 'admin', 'name': 'Administrator'},
    {'uid': 'alice', 'pwd': 'alicesecret', 'name': 'Alice', 'mail': 'alice@example.com'},
    {'uid': 'bob', 'pwd': 'bobsecret', 'name': 'Bob', 'mail': 'bob@example.com'},
    {'uid': 'eve', 'pwd': 'evesecret', 'name': 'Eve', 'ro' : 'True'},
]

################################################################################
# Add a list of groups to the default configuration
#
# A group is defined by the following parameters:

#   name(*)       :   name of the group
#   comments      :   group description
#   users         :   group's members uid list, must exist in USERS
#   level         :   admin = 3, user = 2 (default), dashboard = 1
#
# Parameters not marqued by (*) are optionals
#
REMOVE_PREVIOUS_GROUPS = True
GROUPS = [
    {'name': 'Admins', 'comments': 'The administrators', 'users': ['admin', 'bob'], 'level': 3},
    {'name': 'Users', 'comments': 'The users', 'users': ['alice', 'eve'], 'level': 2},
]

################################################################################
# Add a list of roles to the default configuration
#
# A role is defined by the following parameters:
#   name(*)       :   name of the role
#   group(*)      :   name of the designated group, must exist in GROUPS
#   supervisor(*) :   uid of the user designated as supervisor, must exist in USERS
#   description   :   group description
#
# Parameters not marqued by (*) are optionals
#
REMOVE_PREVIOUS_ROLES = True
ROLES = [
    {'name': 'ServerAdmins', 'group': 'Admins', 'supervisor':  'bob', 'description': 'OS Administrators'},
    {'name': 'NetworkAdmins', 'group': 'Admins', 'supervisor': 'bob', 'description': 'Network Administrators'},
]

################################################################################
# Add a list of IP address to the default configuration
#
# A IP address is defined by the following parameters:
#   addr(*)       :   IPv4 address in dot-decimal notation
#   retries       :   number of retries before considered as down
#   timeout       :   time in milisecond before a try fail
#
# Parameters not marqued by (*) are optionals
#
REMOVE_PREVIOUS_ADDRESSES = True
ADD_ADDRESSES = [
    {'addr': '192.168.1.13'},
    {'addr': '192.168.1.37'},
]

################################################################################
# Include a list of IP address to the default configuration
#
# A range is defined by the following parameters:
#   begin(*)      :   first IPv4 address in dot-decimal notation
#   end(*)        :   last IPv4 address in dot-decimal notation
#   retries       :   number of retries before considered as down
#   timeout       :   time in milisecond before a try fail
#
# Parameters not marqued by (*) are optionals
#
REMOVE_PREVIOUS_INCLUDE_RANGES = True
INCLUDE_RANGES = [
    {'begin': '192.168.0.1', 'end': '192.168.0.254'},
]

################################################################################
# Exclude a list of IP address from the default configuration
#
# A range is defined by the following parameters:
#   begin(*)      :   first IPv4 address in dot-decimal notation
#   end(*)        :   last IPv4 address in dot-decimal notation
#
# Parameters not marqued by (*) are optionals
#
REMOVE_PREVIOUS_EXCLUDE_RANGES = True
EXCLUDE_RANGES = [
#    {'begin': '10.0.2.0', 'end': '10.0.2.255'},
]

################################################################################
# Set the status of one or more of the following services:
#   NOTIFICATION, SNMP, WMI (OpenNMS > 1.7)
#
# A status is defined by one of the following value:
#   True | False
#
NOTIFICATION = True
WMI = True
SNMP = True
SNMP_THRESHOLDING = True

################################################################################
# Add SNMP credentials to the default configuration
#
# A SNMP credential is defined by the following parameters:
#   community     :   the community string for SNMP queries, default "public"
#   version       :   "v1", "v2c", or "v3", default "v1"
#   port          :   overrides the default port of 161
#   begin         :   first IPv4 address in dot-decimal notation
#   end           :   last IPv4 address in dot-decimal notation
#
# Parameters not marqued by (*) are optionals
#
# A SNMP credential with 'begin' but no 'end' parameters is valid
# and refer to a specific IP address
#
REMOVE_PREVIOUS_SNMP_CREDENTIALS = True
SNMP_CREDENTIALS = [
    {'community': 'public', 'version': 'v2c'},
    {'community': 'public', 'begin': '192.168.0.10', 'end': '192.168.0.19', 'version': 'v1'},
    {'community': 'private', 'begin': '192.168.1.13'},
    {'community': 'private', 'begin': '192.168.1.37'},
]

################################################################################
# Add WMI credentials to the default configuration (OpenNMS > 1.7)
#
# A WMI credential is defined by the following parameters:
#   username(*)   :   username
#   domain(*)     :   domain
#   password(*)   :   password in plaintext
#   begin         :   first IPv4 address in dot-decimal notation
#   end           :   last IPv4 address in dot-decimal notation
#
# Parameters not marqued by (*) are optionals
#
# There must be one and one only WMI credential whitout 'begin' and
# 'end' parameters whish is the default  user information.
#
# A WMI credential with 'begin' but no 'end' parameters is valid
# and refer to a specific IP address
#
# The order is important, a new rule will overwrite any part of an old rule
# it can replace.
# Ex:
#     If we define [192.168.0.1-192.168.0.254] for user A and [192.168.0.8] for
#     user B, user A will get [192.168.0.1-192.168.0.7] and
#     [192.168.0.7-192.168.0.254].
#
#
REMOVE_PREVIOUS_WMI_CREDENTIALS = True
WMI_CREDENTIALS = [
#    {'username': 'wmiuser', 'domain': 'EXAMPLE', 'password': 'secret'},
]

################################################################################
# Add a list of plugin to the default configuration
#
# One plugin name must be equal to his python filename in the plugins directory.
PLUGINS = ["apache",  "nginx", "syslog", "ldap"]
PROCESS = [
    {"name": "PostgreSQL", "value": "postgres"},
    {"name": "Apache", "value": "apache2"},
    {"name": "MySQL", "value": "mysqld"},
    {"name": "SSH", "value": "sshd"},
    {"name": "SendMail", "value": "sendmail"},
    {"name": "Oracle", "value": "oracle"},
    {"name": "VSFTP", "value": "vsftpd"},
    {"name": "SMB", "value": "smbd"},
]
WIN32_SERVICES = [
    {"name": "Server", "value": "Server"},
]
#TODO add "specific" parameter
ORACLE_INSTANCE_LINUX = [
    {"name": "Database", "value": "ora_pmon_DATABASE"},
]

################################################################################
# Add LDAP uers to the default configuration
#
# LDAP_USERNAME and LDAP_PASSWORD define creditentials for searching in LDAP.
#
# LDAP_USERS_KEYS is used to populate OpenNMS database from LDAP.
# It contains relation between OpenNMS User (see USERS above) and attribute
# from an LDAP entry:
#   {'opennms_user_attr1': 'ldap_attr1', 'opennms_user_attr2': 'ldap_attr2'}
#
# LDAP_USERS_GROUP and LDAP_USERS_PASSWORD are the group and password assigned
# to all LDAP users.
#
# LDAP_DOMAIN is the distinguished name to use as the search base.
#
# LDAP_FILTER_USER is the organizational unit where the users are stored.
#
# LDAP_FILTER_ROLE is the common name wich users must be member of to login.
#

#LDAP_ADDRESS = '192.168.0.2'
#LDAP_PORT = 389
#LDAP_USERNAME = 'usersearch'
#LDAP_PASSWORD = 'secret'
#LDAP_USERS_KEYS = {'uid': 'sAMAccountName', 'name': 'cn', 'mail': 'mail'}
#LDAP_USERS_GROUP = 'Admins'
#LDAP_USERS_PASSWORD = 'secret'
#LDAP_USERS_READ_ONLY = False

#LDAP_DOMAIN = 'dc=example,dc=com'
#LDAP_FILTER_USER = 'ou=IT,ou=Example'
#LDAP_FILTER_ROLE = 'cn=OpenNMS'

################################################################################
# Configure Mail notification
#
# MAIL_NAME is the name of this configuration.
#
# MAIL_SERVER should be an IP address or the DNS name of the mail server.
#
# MAIL_ADDRESS is the mail address given to OpenNMS readable with MAIL_USERNAME
# and MAIL_PASSWORD credentials.
#
MAIL_NAME = "example"
MAIL_SERVER = "mail.example.com"
MAIL_ADDRESS = "opennms@example.com"
MAIL_USERNAME = "opennms"
MAIL_PASSWORD = "secret"