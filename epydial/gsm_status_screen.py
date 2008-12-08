#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class GsmStatusScreen(EdjeGroup):
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, GSM_STATUS_SCREEN_NAME)

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("power_status_gsm", self.on_power_status_gsm)
		PyneoController.register_callback("device_status", self.on_device_status)
		PyneoController.register_callback("gsm_details", self.on_gsm_details)
		PyneoController.register_callback("scan_operator", self.on_scan_operator)
		PyneoController.register_callback("brightness_change", self.on_brightness_change)

	def on_scan_operator(self, status):
		operator = 'scan operator:<br>'
		for n, v in status.items():
			operator += v['oper'] + '<br>' 
			print 'provider', n, ':', v['oper']
		self.part_text_set("scan_operator_caption", operator)

	def on_brightness_change(self, status):
		self.part_text_set("description_brightness", "brightness %s"%status+"%")

	def on_device_status(self, status):
		self.part_text_set("device_caption", \
			"imei: %s<br>model: %s<br>revision: %s<br>manufacturer: %s" \
			%(status['imei'], status['model'], status['revision'], status['manufacturer']))

	def on_gsm_details(self, status):
		global oper, lac, ci, rssi, mcc, cc, country
		if status.has_key('oper'):
			oper = status['oper']
		if status.has_key('lac'):
			lac = status['lac']
		if status.has_key('ci'):
			ci = status['ci']
		if status.has_key('rssi'):
			rssi = status['rssi']
		if status.has_key('mcc'):
			mcc = status['mcc']
			connection = connect(DB_FILE_PATH)
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM mcc WHERE mcc='" + str(mcc) + "'")
			for row in cursor:
				country = row[0]
				cc = row[1]
		self.part_text_set("gsm_details_caption", \
			"operator: %s<br>lac/ci: %s/%s<br>rssi: %s<br>mcc/cc/country: %s/%s/%s" \
			%(oper, lac, ci, rssi, mcc, cc, country))

	def on_power_status_gsm(self, status):
		if status: p_status = "on"
		else: p_status = "off"
		print '--- gsm device is ', p_status
		self.part_text_set("button_11_caption", p_status)
		self.part_text_set("pwr_caption", "gsm device is %s"%p_status)

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		status = self.part_text_get("button_11_caption")
		if source == "headline":
			PyneoController.scan_operator()
		if source == "button_12":
			PyneoController.show_dialer_screen()
		elif source == "on" and  status == "on":
			PyneoController.power_down_gsm()
		elif source == "on" and status == "off":
			PyneoController.power_up_gsm()
#		elif source == "button_right_bg_brightness":
#			PyneoController.brightness_change(source)
#		elif source == "button_left_bg_brightness":
#			PyneoController.brightness_change(source)

