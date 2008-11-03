#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class InCallScreen(EdjeGroup):
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, INCALL_SCREEN_NAME)

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("gsm_number_display", self.on_gsm_number_display)

	def on_gsm_number_display(self, number):
		self.part_text_set("incall_number_text", number)

	@edje.decorators.signal_callback("dialer_incall_send", "*")
	def on_edje_signal_dialer_incall_triggered(self, emission, source):
		if source == "Hangup Call":
			print source
			PyneoController.gsm_hangup()
		if source == "Accept Call":
			print source
			PyneoController.gsm_accept()

