#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
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
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		try:
			cursor.execute("SELECT * FROM contacts WHERE mobil LIKE %s OR home LIKE %s OR work LIKE %s" % (number, number, number))
			for row in cursor:
				CallerNamemap = row[0], row[1], row[2], row[3], row[4]

			if CallerNamemap[2] == str(number): source = 'mobil'
			elif CallerNamemap[3] == str(number): source = 'home'
			elif CallerNamemap[4] == str(number): source = 'work'

			if CallerNamemap[1] and CallerNamemap[0]:
				self.part_text_set("incall_number_text", "%s: %s, %s" % (source, CallerNamemap[1], CallerNamemap[0]))
		except:
			self.part_text_set("incall_number_text", "??? %s ???" % number)

	@edje.decorators.signal_callback("dialer_incall_send", "*")
	def on_edje_signal_dialer_incall_triggered(self, emission, source):
		if source == "Hangup Call":
			PyneoController.stop_ringtone()
			PyneoController.gsm_hangup()
		if source == "Accept Call":
			PyneoController.stop_ringtone()
			PyneoController.gsm_accept()
		print source
