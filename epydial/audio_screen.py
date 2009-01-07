#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class AudioScreen(EdjeGroup):
	toggle = 0

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, AUDIO_SCREEN_NAME)
		PyneoController.get_mp3_tags()

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("on_get_mp3_tags", self.on_get_mp3_tags)

	def on_get_mp3_tags(self, status):
		self.part_text_set("mp3_tags", "artist: %s<br>album: %s<br>title: %s" % (status['artist'], status['album'], status['title']))

	@edje.decorators.signal_callback("music_player_send", "*")
	def on_edje_signal_audio_screen_triggered(self, emission, source):
#		if source == "button_play_pause":
#			self.signal_emit("button_play_pause", " ")
#			PyneoController.pause_music()
#			PyneoController.show_dialer_screen()
		if source == "play_pause":
			if self.toggle == 0:
				self.signal_emit("key1", "")
				PyneoController.play_music()
				self.toggle = 1
			elif self.toggle == 1:
				self.signal_emit("key2", "")
				PyneoController.pause_music()
				self.toggle = 0
			PyneoController.get_mp3_tags()
		if source == "stop":
			self.signal_emit("key2", "")
			PyneoController.pause_music()
			self.toggle = 0
			PyneoController.stop_music()
			PyneoController.get_mp3_tags()
		if source == "track_right":
			PyneoController.next_music()
			PyneoController.get_mp3_tags()
		if source == "track_left":
			PyneoController.previous_music()
			PyneoController.get_mp3_tags()
		print 'source: ', source
