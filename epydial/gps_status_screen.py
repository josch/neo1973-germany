#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class GpsStatusScreen(EdjeGroup):
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, GPS_STATUS_SCREEN_NAME)
		self.first = 0.0
		self.last = 0.0

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("power_status_gps", self.on_power_status_gps)
		PyneoController.register_callback("gps_position_change", self.on_gps_position_change)

	def on_power_status_gps(self, status):
		if status: p_status = "on"
		else: p_status = "off"
		print '--- gps device is ', p_status
		self.part_text_set("button_11_caption", p_status)
		self.part_text_set("gps_caption", "gps device is %s"%p_status)

	def on_gps_position_change(self, status):
		if status['fix'] == 1:
			self.last = time.time()
			print 'TIME TO FIX: ', self.last-self.first
			self.part_text_set("gps_caption", "fix: %s<br>long/lat: %f/%f<br>altitude: %d<br>kph/course: %d/%d<br>satellites: %s"%(status['fix'], status['longitude'], status['latitude'], status['altitude'], status['kph'], status['course'], status['satellites']))
		else:
			self.part_text_set("gps_caption", "fix: NIX FIX")
		
	@edje.decorators.signal_callback("gps_send", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		status = self.part_text_get("button_11_caption")
		if source == "<":
			PyneoController.show_dialer_screen()
		if source == "on" and  status == "on": PyneoController.power_down_gps()
		elif source == "on" and status == "off":
			self.first = time.time()
			PyneoController.power_up_gps()


