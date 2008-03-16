"""
 * SysFSAccess.py - SettingsGUI - tools to access SysFS
 *
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
 
def set_sysfs_value(entry_dir, value):
    try:
        file_descriptor = open(entry_dir, 'w')
    except:
        return False
    file_descriptor.write("%d" % int(value))
    file_descriptor.close()
    return True

def get_sysfs_value(entry_dir):
    try:
        file_descriptor = open(entry_dir)
    except:
        return ""
    value = file_descriptor.read()
    file_descriptor.close()
    return value
