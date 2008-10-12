#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class HonScreen(EdjeGroup):
	class Tile(evas.Image):
		def __init__(self, canvas):
			evas.Image.__init__(self, canvas)
			self.show()

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, HON_SCREEN_NAME)

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("get_hon", self.on_get_hon)

	def on_get_hon(self, status):
		print '--- get hotornot pix'
		print '--- pix', status['img']
		self.part_text_set("hon_caption", "nick: %s<br>%s"%(status['nick'], status['img']))

	@edje.decorators.signal_callback("hon_send", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		status = self.part_text_get("button_11_caption")
		if source == "<":
			PyneoController.show_dialer_screen()

