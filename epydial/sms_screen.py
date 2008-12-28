#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class SmsScreen(EdjeGroup):
	sms_offset = 0
	sorted_by = 'REC UNREAD'
	detail = False

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, SMS_SCREEN_NAME)
		if self.check_for_unread() == 0:
			self.sorted_by = 'REC READ'
		elif self.check_for_unread() <> 0:
			self.sorted_by = 'REC UNREAD'
		self.show_sms()

	def del_displayed_sms(self):
		x=1
		while x < 5:
			self.part_text_set("sms_status_%s" %x, "")
			self.part_text_set("sms_time_number_%s" %x, "")
			self.part_text_set("sms_text_%s" %x, "")
			x += 1

	def check_for_unread(self):
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		cursor.execute("SELECT COUNT(*) FROM sms WHERE status='REC UNREAD'")
		for row in cursor:
			print 'Count: ', row[0]
		return row[0]

	def show_sms(self):
		x = 1
		self.detail = False
		self.del_displayed_sms()
		self.part_text_set("sort_by", "sorted by: %s" %self.sorted_by)
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM sms WHERE status='%s' ORDER BY time DESC LIMIT 4 OFFSET %s" %(self.sorted_by, self.sms_offset))
		for row in cursor:
			if row[0] == 'REC UNREAD':
				read_status = 'U: '
			elif row[0] == 'REC READ':
				read_status = 'R: '
			self.part_text_set("sms_status_%s" %x, "%s" %read_status)
			self.part_text_set("sms_time_number_%s" %x, "%s, %s" %(row[2][:14], row[1]))
			self.part_text_set("sms_text_%s" %x, row[3])
			x += 1

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		if self.detail == False:
			if source == "1":
				PyneoController.show_sms_screen_detail()
				PyneoController.show_sms_detail(self.sms_offset, self.sorted_by)
			if source == "2":
				self.sms_offset += 1
				PyneoController.show_sms_screen_detail()
				PyneoController.show_sms_detail(self.sms_offset, self.sorted_by)
			if source == "3":
				self.sms_offset += 2
				PyneoController.show_sms_screen_detail()
				PyneoController.show_sms_detail(self.sms_offset, self.sorted_by)
			if source == "4":
				self.sms_offset += 3
				PyneoController.show_sms_screen_detail()
				PyneoController.show_sms_detail(self.sms_offset, self.sorted_by)
			if source == "button_10":
				PyneoController.show_dialer_screen()
			if source == "button_12":
				self.sms_offset += 4
				self.show_sms()
			if source == "button_11":
				self.sms_offset -= 4
				self.show_sms()
			if source == "headline" and self.sorted_by == "REC UNREAD":
				self.sorted_by = 'REC READ'			
				self.sms_offset = 0
				self.show_sms()
			elif source == "headline" and self.sorted_by == "REC READ":
				self.sorted_by = 'REC UNREAD'
				self.sms_offset = 0
				self.show_sms()
		print 'source: ', source

