#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class PixScreen(EdjeGroup):
	pix_pointer = 0

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, PIX_SCREEN_NAME)

		self.objects = os.listdir(PIX_FILE_PATH)
		self.part_text_set("filename", self.objects[self.pix_pointer])

		self.on_get_pix()

	def on_get_pix(self):
		self.image = self.evas.Image(file=PIX_FILE_PATH + self.objects[self.pix_pointer])
		print 'pix: ', self.objects[self.pix_pointer]
		x, y = self.image.image_size
		dx, dy = self.part_size_get('clipper')
		print 'x, y, dx, dy: ', x, y, dx, dy
		if x * dy > y * dx:
			y = y * dx / x
			x = dx
		else:
			x = x * dy / y
			y = dy
		print 'x, y, dx, dy: ', x, y, dx, dy
		self.image.fill = (361-x)/2, (361-y)/2, x, y
		self.part_swallow('icon', self.image)
		self.obj = self.part_object_get('clipper')
#		self.obj.size = x, y
		self.obj.geometry = 60+(361-x)/2, 140+(361-y)/2, x, y
		self.obj.show()
		print 'obj: ', self.obj

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		if source == "pre":
			self.image.delete()
			self.pix_pointer += 1
			self.part_text_set("filename", self.objects[self.pix_pointer])
			self.on_get_pix()
		if source == "rev":
			self.image.delete()
			self.pix_pointer -= 1
			self.part_text_set("filename", self.objects[self.pix_pointer])
			self.on_get_pix()
		if source == "button_10":
			self.image.delete()
			PyneoController.show_dialer_screen()
		print 'source: ', source

