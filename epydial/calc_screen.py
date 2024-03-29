#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class CalcScreen(EdjeGroup):
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, CALC_SCREEN_NAME)

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_calc_screen_triggered(self, emission, source):
		if source == "background":
			PyneoController.show_dialer_screen()

