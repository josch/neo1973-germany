#!/usr/bin/python
#coding=utf8

import os
import sys
import math
import time

z = 10

def download(x,y,z):
    import urllib
    try:
        webFile = urllib.urlopen("http://a.tile.openstreetmap.org/%d/%d/%d.png"%(z,x,y))
        if not os.path.exists("%d"%z):
            os.mkdir("%d"%z)
        if not os.path.exists("%d/%d"%(z,x)):
            os.mkdir("%d/%d"%(z,x))
        localFile = open("%d/%d/%d.png"%(z,x,y), 'w')
        localFile.write(webFile.read())
        webFile.close()
        localFile.close()
    except Exception, e:
        print e
        
def lon2km(lat):
    return math.cos(lat*math.pi/180)*2*math.pi*6378.137/360

def getxy(lat,lon,z):
    x = (lon+180)/360 * 2**z
    y = (1-math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi)/2 * 2**z
    return int(x),int(y)
    
lat = 49.009051
lon = 8.402481

r = 10

lat1 = lat-r/111.32
lon1 = lon-r/lon2km(49.009051)
lat2 = lat+r/111.32
lon2 = lon+r/lon2km(49.009051)

tiles = 0
#do not download zoom 18
for z in range(5,18):
    x1,y1 = getxy(lat1, lon1, z)
    x2,y2 = getxy(lat2, lon2, z)
    tiles += (x2-x1)*(y1-y2)
    
print "do you really want to download %d tiles? [Y/n]"%tiles,
data = sys.stdin.read(1)
if data in ("y", "Y"):
    i = 1;
    for z in range(5,18):
        x1,y1 = getxy(lat1, lon1, z)
        x2,y2 = getxy(lat2, lon2, z)
        for x in xrange(x1,x2+1):
            for y in xrange(y2,y1+1):
                if not os.path.exists("%d/%d/%d.png"%(z,x,y)):
                    download(x,y,z)
                print "\r%i"%i,
                sys.stdout.flush()
                i+=1
