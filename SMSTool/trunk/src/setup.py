#!/usr/bin/python
"""
 * setup.py - script to install SettingGUI
 * (C) 2007 by Kristian Mueller <kristian-m@kristian-m.de>
 * All Rights Reserved
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from distutils.core import setup
import os

setup(name='SMSTool',
        description='GUI for SMS handling',
        long_description='GUI to read and write SMS on FIC1973 (OpenMoko Distribution)',
        author='Kristian Mueller',
        author_email='kristian-m@kristian-m.de',
        url='http://wiki.openmoko.org/wiki/SMSTool',
        version='0.3c',
        license='GPL_v2',
        scripts=['SMSTool.py'],
        package_dir = {"smstool" : ""},
        packages = ["smstool"],
    )
