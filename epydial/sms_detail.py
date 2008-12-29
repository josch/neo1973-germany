#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class SmsDetail(EdjeGroup):

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, SMS_DETAIL_SCREEN_NAME)

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("show_sms_detail", self.on_show_sms_detail)

	def mark_sms_read(self, sms_time):
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		cursor.execute("UPDATE sms SET status='REC READ' WHERE time='%s'" %(sms_time))
		connection.commit()

	def on_show_sms_detail(self, sms_number, sms_status):
		self.sms_offset = sms_number
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM sms WHERE status='%s' ORDER BY time DESC LIMIT 1 OFFSET %s" %(self.sms_offset, sms_number))
		for row in cursor:
			self.part_text_set("sms_text_1", row[2] + '<br>' + row[1] + '<br>' + row[3])

		if row[0] == 'REC UNREAD':
			self.mark_sms_read(row[2])

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		if source == "button_10":
			PyneoController.show_dialer_screen()
		if source == "button_11":
			self.sms_offset -= 1
			PyneoController.show_sms_detail(self.sms_offset, self.sorted_by)
		if source == "button_12":
			self.sms_offset += 1
			PyneoController.show_sms_detail(self.sms_offset, self.sorted_by)
		print 'source: ', source

