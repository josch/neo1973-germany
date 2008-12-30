#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

ZIP_CODE = 'GMXX0007' #GMXX0007 Berlin, GMXX0049 Hamburg
TEMP_UNIT = 'c'

WEATHER_URL = 'http://xml.weather.yahoo.com/forecastrss?p=%s&u=%s'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'

from epydial import *
import urllib
from xml.dom import minidom

class WeatherScreen(EdjeGroup):
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, WEATHER_SCREEN_NAME)
		self.weather_for_zip(ZIP_CODE, TEMP_UNIT)

	def on_get_pix(self, icon):
		self.image = self.evas.Image(file=PIX_WEATHER_FILE_PATH + icon + '.png')
		x, y = self.image.image_size
		dx, dy = self.part_size_get('clipper')
		print 'x, y, dx, dy: ', x, y, dx, dy
		if x * dy > y * dx:
			y = y * dx / x
			x = dx
		else:
			x = x * dy / y
			y = dy
		print 'x, y, dx, dy: ', x, y, dx, dy
		self.image.fill = 0, 0, x, y
		self.part_swallow('icon', self.image)
		self.obj = self.part_object_get('clipper')
		self.obj.size = x, y
		self.obj.show()
		print 'obj: ', self.obj

	def weather_for_zip(self, zip_code, unit):
		url = WEATHER_URL % (zip_code, unit)
		dom = minidom.parse(urllib.urlopen(url))
		forecasts = []
		for node in dom.getElementsByTagNameNS(WEATHER_NS, 'forecast'):
			forecasts.append({
				'date': node.getAttribute('date'),
				'low': node.getAttribute('low'),
				'high': node.getAttribute('high'),
				'condition': node.getAttribute('text'),
				'code': node.getAttribute('code'),
			})
		ycondition = dom.getElementsByTagNameNS(WEATHER_NS, 'condition')[0]

		self.on_get_pix(ycondition.getAttribute('code'))
		self.part_text_set("location", dom.getElementsByTagName('title')[0].firstChild.data[17:])
		self.part_text_set("current", "current condition: %s<br>current temp: %s" % (ycondition.getAttribute('text'), ycondition.getAttribute('temp')))
		self.part_text_set("forecasts", "forecasts:<br>date: %s<br>low: %s<br>high: %s<br>condition: %s" % (forecasts[1]['date'], forecasts[1]['low'], forecasts[1]['high'], forecasts[1]['condition']))

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		if source == "button_12":
			self.image.delete()
			PyneoController.show_dialer_screen()
		if source == "headline":
			self.image.delete()
			self.weather_for_zip(ZIP_CODE, TEMP_UNIT)
		print 'source: ', source
