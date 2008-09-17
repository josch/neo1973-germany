# PyTrackerClient.py
'''
author: edistar
license: GPL v3 or later
version 0.1
'''
from __future__ import with_statement
import datetime
import ecore
import e_dbus
import os
import sys
from socket import *
from dbus import SystemBus, Interface
from optparse import OptionParser

class TrackClient:

	def __init__(self, username='anonymous', passwordhash='', host='localhost', port='49152'):
                self.InitSocket(host, port)
                self.InitDbusStuff()
                self.InitUserHash(username, passwordhash)

        def InitSocket(self, host, port):

# Set the socket parameters
# e.g.	        host = "localhost"
# e.g.	        port = 49152
        	self.__addr = (str(host),int(port))

# Create socket
                self.__UDPSock = socket(AF_INET,SOCK_DGRAM)

# Debug message:
                print "UDP Socket for %s at port %s created" % (host, port)


        def TransmitUDP(self, data):
                if data:
                        self.__UDPSock.sendto(data,self.__addr)

# Debug message:
                        print "UDP stream %s sent" % (data)

        def CloseSocket(self):
                self.__UDPSock.close()

# Debug message:
#               print "UDP Socket closed"


        def InitDbusStuff(self):

# get FSO Usage proxy/iface up to request GPS
		self.systembus=systembus = SystemBus(mainloop=e_dbus.DBusEcoreMainLoop())
		self.usage_proxy = self.systembus.get_object('org.freesmartphone.ousaged', '/org/freesmartphone/Usage')
		self.usage_iface = Interface(self.usage_proxy, 'org.freesmartphone.Usage')

# request GPS from FSO (which then powers on the GPS chip)
		self.usage_iface.RequestResource("GPS")

# get gypsy proxy/iface up
		self.ogpsd_proxy = self.systembus.get_object('org.freesmartphone.ogpsd', '/org/freedesktop/Gypsy')
		self.course_iface = Interface(self.ogpsd_proxy, 'org.freedesktop.Gypsy.Course')
		self.pos_iface = Interface(self.ogpsd_proxy, 'org.freedesktop.Gypsy.Position')


        def UpdateData(self, fields, timestamp, lat, lon, alt):
# get UTC time from gypsy timestamp
		string = str(datetime.datetime.utcfromtimestamp(timestamp))

		date, time = string.split()
		utctime = "%sT%sZ" % (date, time)

# prepare data for sending
	        UDPData = "%s,%s,%s,%s" % (lat, lon, alt, utctime)
                self.SendData(self.__username, self.__pwhash, 'TRANSMIT', UDPData)

# Debug message:
#                print "Updated Data"

        def InitUserHash(self, username, pwhash):

# set username and password globally in the class
                self.__username = username
                self.__pwhash = pwhash
                self.SendData(self.__username, self.__pwhash, action="START")

        def SendData(self, username, pwhash, action, data=""):

# put together and send data to TransmitUDP()
                senddata = "%s;%s;%s;%s" % (username, pwhash, action, data)
                self.TransmitUDP(senddata)


	def StartTrack(self):
		self.SendData(self.__username, self.__pwhash, action="START")

# call self.UpdatePosition() when a dbus signal "PositionChanged" comes along the system bus
		self.terminator = self.pos_iface.connect_to_signal("PositionChanged", self.UpdateData)

		
        def StopTrack(self):
                self.SendData(self.__username, self.__pwhash, action="STOP")
		self.terminator.remove()
                self.usage_iface.ReleaseResource("GPS")
		sys.exit()
