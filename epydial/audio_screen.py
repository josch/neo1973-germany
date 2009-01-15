#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

LICENSE_KEY = "18C3VZN9HCECM5G3HQG2"
ASSOCIATE = "webservices-20"

from epydial import *
import urllib
from xml.dom import minidom

class AudioScreen(EdjeGroup):
	toggle = 0
	volume = 0.9

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, AUDIO_SCREEN_NAME)
		PyneoController.set_volume(self.volume)
		self.part_text_set("volume_label", "volume %d%%" % (self.volume*100))

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("on_get_mp3_tags", self.on_get_mp3_tags)

	def on_get_mp3_tags(self, status):
		self.part_text_set("mp3_tags", "artist: %s<br>album: %s<br>title: %s" % (status['artist'], status['album'], status['title']))
		print 'cover url: ', self.get_amazon_cover(status['artist'] + " "+ status['album'])
 
	def getText(self, nodelist):
		rc = ""
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + node.data
		return rc

	def get_amazon_cover(self, album):
		AMAZON_URL = "http://ecs.amazonaws.de/onca/xml"\
			"?Service=AWSECommerceService"\
			"&AWSAccessKeyId=" + LICENSE_KEY +\
			"&AssociateTag=" + ASSOCIATE +\
			"&ResponseGroup=Images,ItemAttributes"\
			"&Operation=ItemSearch"\
			"&ItemSearch.Shared.SearchIndex=Music"\
			"&ItemSearch.1.Keywords=%s"

		url = AMAZON_URL % (album)
		dom = minidom.parse(urllib.urlopen(url))
		return self.getText(dom.getElementsByTagName("URL")[1].childNodes)

	@edje.decorators.signal_callback("music_player_send", "*")
	def on_edje_signal_audio_screen_triggered(self, emission, source):
		if source == "headline":
			PyneoController.pause_music()
			PyneoController.show_dialer_screen()
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
			self.toggle = 0
			PyneoController.stop_music()
			PyneoController.get_mp3_tags()
		if source == "track_right":
			PyneoController.next_music()
		if source == "track_left":
			PyneoController.previous_music()
		if source == "player-plus":
			self.volume = self.volume + 0.1
			PyneoController.set_volume(self.volume)
			self.part_text_set("volume_label", "volume %d%%" % (self.volume*100))
		if source == "player-minus":
			self.volume = self.volume - 0.1
			PyneoController.set_volume(self.volume)
			self.part_text_set("volume_label", "volume %d%%" % (self.volume*100))
		print 'source: ', source
