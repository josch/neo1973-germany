#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class ContactsScreen(EdjeGroup):
	contact_offset = 0
	sorted_by = 'lastname'
	detail = False

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, CONTACTS_SCREEN_NAME)
		self.show_contacts()

	def del_displayed_contacts(self):
		x=1
		while x < 5:
			self.part_text_set("contact_%s" %x, "")
			x += 1

	def show_contacts(self):
		x = 1
		self.detail = False
		self.del_displayed_contacts()
		self.part_text_set("sort_by", "sorted by: %s" %self.sorted_by)
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM contacts ORDER BY %s LIMIT 4 OFFSET %s" %(self.sorted_by, self.contact_offset))
		for row in cursor:
			self.part_text_set("contact_%s" %x, "%s, %s" %(row[1], row[0]))
			x += 1

	def show_contact_detail(self, detail_offset):
		self.part_text_set("sort_by", "detail view")
		self.detail = True
		self.del_displayed_contacts()
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM contacts ORDER BY %s LIMIT 1 OFFSET %s" %(self.sorted_by, detail_offset))
		for row in cursor:
			self.part_text_set("contact_1", "%s, %s" %(row[1], row[0]))
			self.part_text_set("contact_2", "mobil: %s" %row[2])
			self.part_text_set("contact_3", "home: %s" %row[3])
			self.part_text_set("contact_4", "work: %s" %row[4])

	@edje.decorators.signal_callback("mouse,up,1", "*")
	def on_edje_signal_dialer_status_triggered(self, emission, source):
		if self.detail == True:
			if source == "button_10":
				self.contact_offset = 0
				self.show_contacts()
			if source == "button_12":
				self.contact_offset += 1
				self.show_contact_detail(self.contact_offset)
			if source == "button_11":
				self.contact_offset -= 1
				self.show_contact_detail(self.contact_offset)
			if source == "2":
				PyneoController.gsm_dial(self.part_text_get("contact_2")[7:])
			if source == "3":
				PyneoController.gsm_dial(self.part_text_get("contact_3")[6:])
			if source == "4":
				PyneoController.gsm_dial(self.part_text_get("contact_4")[6:])
		elif self.detail == False:
			if source == "1":
				self.show_contact_detail(self.contact_offset)
			if source == "2":
				self.contact_offset += 1
				self.show_contact_detail(self.contact_offset)
			if source == "3":
				self.contact_offset += 2
				self.show_contact_detail(self.contact_offset)
			if source == "4":
				self.contact_offset += 3
				self.show_contact_detail(self.contact_offset)
			if source == "button_10":
				PyneoController.show_dialer_screen()
			if source == "button_12":
				self.contact_offset += 4
				self.show_contacts()
			if source == "button_11":
				self.contact_offset -= 4
				self.show_contacts()
			if source == "headline" and self.sorted_by == "lastname":
				self.sorted_by = 'firstname'			
				self.contact_offset = 0
				self.show_contacts()
			elif source == "headline" and self.sorted_by == "firstname":
				self.sorted_by = 'lastname'
				self.contact_offset = 0
				self.show_contacts()
		print 'source: ', source

