#!/usr/bin/python
'''
authors: edistar
license: gpl v2 or later
version 0.2
'''

from __future__ import with_statement
import time
import datetime
import ecore
import e_dbus
import os
from dbus import SystemBus, Interface
from optparse import OptionParser

class Main:

        def __init__(self):

		self.GetPath()

# get FSO Usage proxy/iface up to request GPS
		self.systembus=systembus = SystemBus(mainloop=e_dbus.DBusEcoreMainLoop())
		self.usage_proxy = self.systembus.get_object('org.freesmartphone.ousaged', '/org/freesmartphone/Usage')
		self.usage_iface = Interface(self.usage_proxy, 'org.freesmartphone.Usage')

# Request GPS from FSO (which then powers on the GPS chip)
		self.usage_iface.RequestResource("GPS")

#get gypsy proxy/iface up
		self.ogpsd_proxy = self.systembus.get_object('org.freesmartphone.ogpsd', '/org/freedesktop/Gypsy')
		self.course_iface = Interface(self.ogpsd_proxy, 'org.freedesktop.Gypsy.Course')
		self.pos_iface = Interface(self.ogpsd_proxy, 'org.freedesktop.Gypsy.Position')

# call self.UpdatePosition() when a dbus signal "PositionChanged" comes along the system bus
		self.pos_iface.connect_to_signal("PositionChanged", self.UpdatePosition)


	def UpdatePosition(self, fields, timestamp, lat, lon, alt):

# get UTC time from gypsy timestamp
		string = str(datetime.datetime.utcfromtimestamp(timestamp))
		date, time = string.split()
		utctime = "%sT%sZ" % (date, time)

# write data to file
		s ="%s,%s,%s,%s\n" % (lat, lon, alt, utctime)
		with open(self.trackfile,'a') as file:
			file.write(s)

#debugging output:
		print s


	def Parser(self):

# parse command line options
		self.parser=OptionParser("usage foo bar")
		self.parser.add_option("-f", "--file", "-o", "-l", action = "store", dest = "trackfile")
		(self.options, self.args) = self.parser.parse_args()


	def GetPath(self):
		trackpath = '.'
		suffix = 'track'
		self.Parser()

# raises an Exception if the path doesn't exist! :)
		path, rubbish, suffix = self.trackfile.options.rpartition("/")

		if not os.path.exists(path):
			raise Exception("path does not exist!")

# sets trackfile path and filename		
		self.trackfile = "%s/%s-%s" % (trackpath, time.strftime(), suffix)



test=Main()
ecore.main_loop_begin()
