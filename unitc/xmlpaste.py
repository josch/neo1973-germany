#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree
from StringIO import StringIO


def xmlpaste(tag):
    file = etree.parse('unit.xml')
    categoryname = 'currency'

    for category in file.findall('//category'):
        if category.get('name') == categoryname:
            for units in category.getchildren():
                print units.get('name')
#    for i in file.getiterator('category'):
#        for f in i.getchildren():
#            print f.get('name')
#    for category  in file.findall('//category'):
#        category.get('name')
#        for i in file.findall('//unit'):
#            i.get('name')
#    print file.findtext('currency')
#        print i.tag, i.text
#        for child in i.getchildren():
#            print i.text
#            print child.get('name')

#    units = []
#    for unit in file.getiterator('unit'): 
#        units.append(unit.text)
#    factors = []
#    for factor in file.getiterator('factor'):
#        factors.append(factor.text)
#    i = 0
#    content = len(units)
#
#    while i != content:
#        print units[i], 
#        print factors[i]
#        i += 1
#
xmlpaste('unit')
