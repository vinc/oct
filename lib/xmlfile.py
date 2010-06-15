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
import xml.dom.minidom

class XMLFile(object):
    """
    This class load a file into an XML DOM tree and save the modifications done
    to it.
    """

    def __init__(self):
        """
        """
        self._rootName = None
        self._doc = None

    @classmethod
    def open(cls, fileName, mode = "r"):
        """
        Parse fileName to an XML tree if exist, otherwise create a new one if
        mode is set to "w".
        """
        #print "DEBUG: open('%s', '%s') ..." % (fileName, mode)
        xml_file = XMLFile()
        xml_file._fileName = fileName
        try:
            xml_file._doc = xml.dom.minidom.parse(fileName)
        except (IOError, xml.parsers.expat.ExpatError), e:
            if mode == "r":
                sys.exit(e)
            elif mode == "w":
                xml_file._doc = xml.dom.minidom.Document()
        except:
            raise
        else:
            xml_file.__clean()
        assert xml_file._doc is not None
        return xml_file

    def get_root(self):
        """
        Find and return the root of the XML tree.
        NB: regardless of self._rootName who is only used internaly.
        """
        ## Root from self._rootName
        #assert self._rootName is not None
        #elems = self._doc.getElementsByTagName(self._rootName)
        #assert elems.length == 1
        #return elems.item(0)
        # Root discovered
        assert self._doc.hasChildNodes()
        root_candidates = list()
        for i in range(self._doc.childNodes.length):
            root = self._doc.childNodes.item(i)
            if root.nodeType == xml.dom.Node.ELEMENT_NODE:
                root_candidates.append(root)
            elif root.nodeType == xml.dom.Node.COMMENT_NODE:
                continue
        assert len(root_candidates) == 1
        return root_candidates[0]
    def set_root(self, tagName):
        """
        Create the root if none exist and fix self._rootName.
        NB: do nothing if a root already exist.
        """
        self._rootName = tagName
        if not self._doc.hasChildNodes():
            root = self._doc.createElement(tagName)
            self._doc.appendChild(root)
        #else:
        #    # What if there is already a root?
    root = property(get_root, set_root)

    def get_document(self):
        """
        Return the Document ...?
        """
        return self._doc

    def __clean_rec(self, node):
        """
        When not using 'xml.dom.ext', the value of a empty attribute is None.
        Change it to "" to prevent toxml() from complaining (Python Bug).
        """
        if node.nodeType == xml.dom.Node.ELEMENT_NODE and node.hasAttributes():
            for i in range(node.attributes.length):
                attr = node.attributes.item(i)
                if attr.value is None:
                    node.setAttribute(attr.name, "")
        for child in node.childNodes:
            self.__clean_rec(child)

    def __clean(self):
        """
        Clean all the tree from the root
        """
        self.__clean_rec(self.root)

    def write(self):
        """
        Write the modifications done to the XML tree to the file.
        """
        f = open(self._fileName, "w")
        f.write(self.read())
        f.close()

    def read(self):
        """
        Convert the XML tree to a string (with the pretty printer from
        Python-XML if exist).
        """
        return self.__str__()

    def __str__(self):
        try:
            from xml.dom.ext import PrettyPrint
            from StringIO import StringIO
        except ImportError:
            print >> sys.stderr, \
                     "Warning: module 'xml.dom.ext' should be installed!"
            return self._doc.toxml('utf-8')
        else:
            tmpStream = StringIO()
            PrettyPrint(self._doc, stream=tmpStream, encoding='utf-8')
            return tmpStream.getvalue()
