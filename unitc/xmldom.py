#!/usr/bin/env python

import xml.dom.minidom

unitfile = 'unit.xml'
file = xml.dom.minidom.parse(unitfile)

name = file.documentElement

for categorynames in file.getElementsByTagName('category'):
    if categorynames.getAttribute('name') == 'length':                 

