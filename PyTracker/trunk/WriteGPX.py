#!/usr/bin/python
'''
authors: Pau1us
license: gpl v2 or later

This is a Class to create *.gpx Files
Usage:
open new file: file = WriteGPX(filename)
write trackpint: file.write(lat, lon, alt, utctime)
close file: file.close()
The file musst be closed, otherwise the file will be incomplete
'''
from __future__ import with_statement

class WriteGPX:
        def __init__(self, filename):
                self.filename = filename
                self.header = '<?xml version="1.0" encoding="UTF-8"?>\n\
<gpx        version="1.1"\n\
        creator="WriteGPX - Python Class used in PyTracker.py"\n\
        xmlns:xsi="http://www.w3.org/XML/1998/namespace"\n\
        xmlns="http://www.topografix.com/GPX/1/1"\n\
        xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">\n\
<trk>\n\
<trkseg>\n'
                self.footer = '</trkseg>\n</trk>\n</gpx>\n'
                
                with open(self.filename,'a') as file:
                        file.write(self.header)
        
        def write(self, lat, lon, ele, time):
                self.trackpoint = '<trkpt lat="%s" lon="%s">\n\
                <ele>%s</ele>\n\
                <time>%s</time>\n\
</trkpt>\n' % (lat, lon, ele, time)
                with open(self.filename,'a') as file:
                        file.write(self.trackpoint)
        
        def close(self):
                with open(self.filename,'a') as file:
                        file.write(self.footer)
