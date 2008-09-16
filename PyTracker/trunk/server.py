from __future__ import with_statement
import time
from socket import *

class TrackServer:
	def __init__(self):
		self.InitHashdb("hashfile.txt")
		self.InitTrackDict()

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

	def VerifyUser(self, username, password_hash):
		for data in self.hashdb:
			if data[0] == username and data[1] == password_hash:
				return 1
		return 0


	def Parser(self, stuff):
#	Parses the complete data sent to UDP port
		try:
			username, password_hash, action, data = stuff.split()
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
		self.TrackDict[username] = "/home/edistar/Openmoko/projects/tracking/data/" + username + time.strftime("%Y%m%d%H%M%S")
		print "Created track", self.TrackDict[username]

	def CloseTrack(self, username):
		self.TrackDict[username] = ""
		print "Closed track", self.TrackDict[username]

	def AddToTrack(self, username, data):
		with open(self.TrackDict[username], "a") as trackfile:
			trackfile.write(data + "\n")
			print "Successfully added data to track", self.TrackDict[username]

instance=TrackServer()

# Set the socket parameters
host = ""
port = 49152
buf = 1024
addr = (host,port)

# Create socket and bind to address
UDPSock = socket(AF_INET,SOCK_DGRAM)
UDPSock.bind(addr)

# Create instance of TrackServer
instance = TrackServer()

#Receive messages
while 1:
        data,addr = UDPSock.recvfrom(buf)
	print "Following data received:", data
	instance.Parser(data)
