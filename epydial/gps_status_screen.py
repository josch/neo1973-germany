#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class GpsStatusScreen(EdjeGroup):
	status_track = "off"
	file_track = None
	trackpoints = None
	track_timer = None

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, GPS_STATUS_SCREEN_NAME)

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
		if status['fix'] == 3:
			self.part_text_set("gps_caption", \
				"fix: %s<br>long/lat: %s/%s<br>altitude: %s<br>kph/course: %s/%s<br>satellites: %s" \
				%(status['fix'], status['longitude'], status['latitude'], status['altitude'], status['kph'], status['course'], status['satellites']))

			if self.status_track == "on" and status['latitude'] and status['longitude']:
				self.trackpoints += 1
				self.track_timer += 1
				self.file_track.write('%s,%s,%s\n' %(self.trackpoints, status['latitude'], status['longitude']))
				self.part_text_set("gps_track", "track log: on<br>trackpoints: %s" %self.trackpoints)
				if self.track_timer == 60:
					self.file_track.flush()
					self.track_timer = 0

		else:
			self.part_text_set("gps_caption", "fix: NIX FIX")

	def start_tracking(self):
		self.status_track = "on"
		self.part_text_set("gps_track", "track log: on")

		if not os.path.exists(TRACK_FILE_PATH):
			os.mkdir(TRACK_FILE_PATH)
		self.file_track = open(TRACK_FILE_PATH + 'track.log', 'w')
		self.trackpoints = self.track_timer = 0

	def stop_tracking(self):
		self.status_track = "off"
		self.part_text_set("gps_track", "track log: off")
		self.file_track.close()
		self.trackpoints = self.track_timer = 0

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		status = self.part_text_get("button_11_caption")
		if source == "headline" and self.status_track == "off":
			self.start_tracking()
		elif source == "headline" and self.status_track == "on":
			self.stop_tracking()
		if source == "button_12":
			PyneoController.show_dialer_screen()
		if source == "button_13":
			pass	#TODO pylgrim integration
		if source == "button_11" and  status == "on":
			PyneoController.power_down_gps()
		elif source == "button_11" and status == "off":
			PyneoController.power_up_gps()

