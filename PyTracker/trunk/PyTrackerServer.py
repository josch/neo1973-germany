#!/usr/bin/env python

from __future__ import with_statement
import time
from socket import *
from WriteGPX import *

class TrackServer:
        def __init__(self, host='', port='49152', hashfile='hashfile', datadir = './'):
                self.InitSocket(host, port)
                self.InitHashdb(hashfile)
                self.InitTrackDict()
                self.datadir = datadir

        def InitHashdb(self, hashfile):
                self.hashdb=[]
                with open(hashfile, "r") as file:
                        for line in file:
                                if line:
                                        self.hashdb.append((line.split()[0], \
                                        line.split()[1]))

        def InitTrackDict(self):
                self.TrackDict={}
                for data in self.hashdb:
                        self.TrackDict[data[0]] = ""

        def InitSocket(self, host, port):

# Set the socket parameters
# e.g.	        host = "localhost"
# e.g.	        port = 49152
                self.__addr = (str(host),int(port))

# Create socket and bind it to the address
                self.UDPSock = socket(AF_INET,SOCK_DGRAM)
                self.UDPSock.bind(self.__addr)

# Debug message:
                print "UDP Socket for %s at port %s created" % (host, port)

        def VerifyUser(self, username, password_hash):
                for data in self.hashdb:
                        if data[0] == username and data[1] == password_hash:
                                return 1
                return 0


        def Parser(self, stuff):

#	Parses the complete data sent to UDP port
                try:
                        username, password_hash, action, data = stuff.split(';')

#			Verifies the user and password
                        if self.VerifyUser(username, password_hash):
                                if action == "START":
                                        self.NewTrack(username)
                                if action == "STOP":
                                        self.CloseTrack(username)
                                if action == "TRANSMIT":
                                        self.AddToTrack(username, data)
                                print "Action", action,"received"
                except:
                        print "Something went wrong.."

        def NewTrack(self, username):
# if a track has already started it needs to be closed (finished)
                if self.TrackDict[username]:
                        self.TrackDict[username].close()
                        print "Track closed because %s requested a new track" % (username)
# start the new track
                self.TrackDict[username] = WriteGPX("%s%s%s" % (self.datadir, username, time.strftime("%Y%m%d%H%M%S")))
                print "Created track %s%s%s" % (self.datadir, username, time.strftime("%Y%m%d%H%M%S"))

        def CloseTrack(self, username):
                if self.TrackDict[username]:
                        self.TrackDict[username].close()
                        print "Closed track", self.TrackDict[username]
                else:
                        print "ha, no track for %s exists!" % (username)

        def AddToTrack(self, username, data):
                lat, lon, ele, time = data.split(',')
                self.TrackDict[username].write(lat, lon, ele, time)


buf = 1024

# Create instance of TrackServer
instance = TrackServer()

#Receive messages
while 1:
        data,addr = instance.UDPSock.recvfrom(1024)
        print "Following data received:", data
        instance.Parser(data)
