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

class IP:
    """
    Class for comparing IP address and do some math with them
    """

    def __init__(self, ip_address):
        """
        Create a new IP object from a given string containing the address
        in quad dotted notation or from an integer.
        """
        try:
            # Assume first that 'ip_address' is in quad dotted notation
            ip_list = ip_address.split('.')
        except AttributeError:
            # Otherwise assume it is an integer
            self._ip_integer = ip_address
        else:
            self._ip_integer = 0
            assert len(ip_list) == 4
            for index, number in enumerate(ip_list):
                self._ip_integer += int(number) * 256 ** (3 - index)

    def __str__(self):
        ip_integer = self._ip_integer
        ip_string = ""
        for exp in range(3, -1, -1):
            ip_string += str(ip_integer / ( 256 ** exp )) + "."
            ip_integer %= 256 ** exp
        return(ip_string.rstrip('.'))

    def __cmp__(self, other):
        ret = self._ip_integer - other._ip_integer
        return sys.maxint if ret > sys.maxint else -sys.maxint \
                          if ret < -sys.maxint else ret

    def __add__(self, num):
        return IP(self._ip_integer + num)

    def __sub__(self, num):
        return IP(self._ip_integer - num)
