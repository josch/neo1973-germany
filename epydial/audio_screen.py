#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
from __future__ import with_statement
__author__ = "M. Dietrich <mdt@pyneo.org>, F. Gau <fgau@gau-net.de>, Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

AMAZON_HOST = 'ecs.amazonaws.de'
AMAZON_PATH = "/onca/xml"
AMAZON_ASSOCIATE = "webservices-20"
AMAZON_LICENSE_KEY = "18C3VZN9HCECM5G3HQG2"

from epydial import *
from httplib import HTTPConnection
from urllib import urlencode
from urlparse import urlparse, urlunparse
from xml.dom.minidom import parseString
from pyneo.dns_support import DNSCache #require: 'export PYTHONPATH=/usr/share/pyneod'

class AudioScreen(EdjeGroup):
	toggle = 0
	volume = 0.1
	position_timer = None
	e_timer = None

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, AUDIO_SCREEN_NAME)
		PyneoController.set_volume(self.volume)
		self.part_text_set("volume_label", "volume %d%%" % (self.volume*100))

	def get_text(self, nodelist):
		return "".join([node.data for node in nodelist if node.nodeType == node.TEXT_NODE])

	def get_content(self, scheme, netloc, path, parameters, query, fragment=None, ):
		http_connection = HTTPConnection(netloc, getaddrinfo=DNSCache.getaddrinfo, timeout=12, )
		try:
			http_connection.request("GET", '%s?%s'% (path, query, ), headers={
				'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
				'Connection': 'close',
				})
			response = http_connection.getresponse()
			if response.status != 200:
				raise Exception(response.reason)
			data = response.read()
		finally:
			http_connection.close()
		return data

	def get_amazon_cover(self, artist, keywords):
		content = self.get_content(
			'http',
			AMAZON_HOST,
			AMAZON_PATH,
			None,
			urlencode((
				("Service", "AWSECommerceService", ),
				("AWSAccessKeyId", AMAZON_LICENSE_KEY, ),
				("AssociateTag", AMAZON_ASSOCIATE, ),
				("ResponseGroup", "Small, Images", ),
				("Operation", "ItemSearch", ),
				("SearchIndex", "Music", ),
				("ContentType", "text/xml", ),
#				("Album", album, ),
				("Artist", artist, ),
				("Keywords", keywords, ), #other search options are welcome
#				("Title", title,),
				)))
		dom = parseString(content)
		url = self.get_text(dom.getElementsByTagName("URL")[1].childNodes)
		data = self.get_content(*urlparse(url))
		return data

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("on_get_mp3_tags", self.on_get_mp3_tags)
		PyneoController.register_callback("on_get_song_duration", self.on_get_song_duration)
		PyneoController.register_callback("on_get_song_position", self.on_get_song_position)

	def on_get_song_position(self, status):
		self.position_timer = status = time.time()
		self.e_timer = ecore.timer_add(1.0, self.display_position)
		self.display_position()

	def on_get_song_duration(self, status):
		self.part_text_set("duration", "%s" % time.ctime(status)[14:][:5])
		print '--- current song length: ', status

	def on_get_mp3_tags(self, status):
		PyneoController.get_song_duration()
#		PyneoController.get_song_position()
		try:
			self.image.delete()
		except:
			pass

		self.part_text_set("mp3_tags", "artist: %s<br>album: %s<br>title: %s" % (status['artist'], status['album'], status['title']))
		if not os.path.isfile(COVER_FILE_PATH + '%s_%s.jpeg' % (status['artist'], status['album'])):
			print '--- cover not exists'
			content = self.get_amazon_cover(status['artist'], status['album'])
			with open(COVER_FILE_PATH + '%s_%s.jpeg' % (status['artist'], status['album']), 'w') as f:
				f.write(content)

		self.image = self.evas.Image(file=COVER_FILE_PATH + '%s_%s.jpeg' % (status['artist'], status['album']))
		x, y = self.image.image_size
		dx, dy = self.part_size_get('icon')
		if x * dy > y * dx:
			y = y * dx / x
			x = dx
		else:
			x = x * dy / y
			y = dy
		print 'x, y, dx, dy: ', x, y, dx, dy
		self.image.fill = 0, 0, x, y
		self.part_swallow('icon', self.image)
		self.obj = self.part_object_get('clipper')
		self.obj.size = x, y
		self.obj.show()

	def display_position(self):
		elapsed = (time.time() - self.position_timer)
		self.part_text_set("position", "%s" % (time.ctime(elapsed)[14:][:5]))
		return True

	@edje.decorators.signal_callback("music_player_send", "*")
	def on_edje_signal_audio_screen_triggered(self, emission, source):
		if source == "headline":
			PyneoController.pause_music()
			PyneoController.show_dialer_screen()
		if source == "play_pause":
			if self.toggle == 0:
				self.signal_emit("key1", "")
				PyneoController.play_music()
				PyneoController.get_mp3_tags()
				self.toggle = 1
			elif self.toggle == 1:
				self.signal_emit("key2", "")
				PyneoController.pause_music()
				self.toggle = 0
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
