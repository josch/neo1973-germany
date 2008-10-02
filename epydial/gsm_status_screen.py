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
		PyneoController.register_callback("pwr_status_change", self.on_pwr_status_change)

	def on_pwr_status_change(self, status):
		self.part_text_set("gsm_caption", "battvolt: %f<br>chgstate: %s"%(status['battvolt'], status['chgstate']))

	def on_power_status_gsm(self, status):
		if status: p_status = "on"
		else: p_status = "off"
		print '--- gsm device is ', p_status
		self.part_text_set("button_11_caption", p_status)
		self.part_text_set("gsm_caption", "gsm device is %s"%p_status)

	@edje.decorators.signal_callback("gsm_send", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		status = self.part_text_get("button_11_caption")
		if source == "<":
			PyneoController.show_dialer_screen()
		if source == "on" and  status == "on": PyneoController.power_down_gsm()
		elif source == "on" and status == "off":
			self.first = time.time()
			PyneoController.power_up_gsm()


