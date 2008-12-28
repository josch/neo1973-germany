#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class HonScreen(EdjeGroup):
	class PixGraph( evas.ClippedSmartObject ):
		def __init__( self, *args, **kargs ):
			evas.ClippedSmartObject.__init__( self, *args, **kargs )

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, HON_SCREEN_NAME)
		self.pixgraph = self.PixGraph( self.evas )
		print 'pixgraph', self.pixgraph

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("get_hon", self.on_get_hon)

	def on_get_hon(self, status):
		img = object_by_url(status['img']).read()
		pix = status['img']
		assert pix.startswith('file://')
		pix = pix[7:]
		self.pix = pix
		self.part_text_set("hon_caption", "nick: %s"%status['nick'])
		self.hot = dict(url=status['hot'])
		self.nothot = dict(url=status['nothot'])

		self.image = self.evas.Image(file=self.pix)
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
		print 'obj: ', self.obj

	def delete(self):
		EdjeGroup.hide(self)

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		if source == "headline":
			PyneoController.get_hon()
		if source == "button_10":
			self.delete()
			PyneoController.show_dialer_screen()
		if source == "button_11":
			self.image.delete()
			PyneoController.vote_hon(self.hot)
			print '---vote hot'
		if source == "button_12":
			self.image.delete()
			PyneoController.vote_hon(self.nothot)
			print '---vote not'
		print 'source: ', source

