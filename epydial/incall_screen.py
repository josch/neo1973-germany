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
		cursor.execute("SELECT * FROM contacts WHERE mobil LIKE '%" + str(number) + "' OR home LIKE '%" + str(number) + "' OR work LIKE '%" + str(number) + "'")
		for row in cursor:
			CallerNamemap = row[0], row[1], row[2], row[3], row[4]

		if CallerNamemap[1] and CallerNamemap[0]:
			self.part_text_set("incall_number_text", "%s"% (CallerNamemap[1] + ', ' + CallerNamemap[0]))
		else:
			self.part_text_set("incall_number_text", "unbekannt")

	@edje.decorators.signal_callback("dialer_incall_send", "*")
	def on_edje_signal_dialer_incall_triggered(self, emission, source):
		if source == "Hangup Call":
			PyneoController.gsm_hangup()
		if source == "Accept Call":
			PyneoController.gsm_accept()
		print source
