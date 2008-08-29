#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = ""
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

WIDTH = 480
HEIGHT = 640
FRAMETIME = 1.0 / 20
FULLSCREEN = True
TITLE = "epydial"
WM_INFO = ("epydial", "epydial")
EDJE_GROUP_NAME = "pyneo/dialer/main"
EDJE_FILE_NAME = "data/themes/dialer.edj"

from datetime import datetime
from dbus import SystemBus
import os
import sys
import time

import e_dbus
import ecore
import ecore.evas
import edje.decorators
import edje
import evas.decorators

from pyneo.dbus_support import *
from pyneo.sys_support import pr_set_name

from ConfigParser import SafeConfigParser

class EdjeGroup(edje.Edje):
	def __init__(self, main, group):
		self.main = main
		
		if not os.path.exists(EDJE_FILE_NAME):
			raise IOError("Edje theme file not found: " + EDJE_FILE_NAME)
		
		try:
			edje.Edje.__init__(self, self.main.evas_canvas.evas_obj.evas, file=EDJE_FILE_NAME, group=group)
		except edje.EdjeLoadError, e:
			raise SystemExit("Error loading %s: %s" % (f, e))
		
		self.size = self.main.evas_canvas.evas_obj.evas.size

class MainScreen(EdjeGroup):
	def __init__(self, main):
		EdjeGroup.__init__(self, main, EDJE_GROUP_NAME)
		self.text = []
		
		dbus_ml = e_dbus.DBusEcoreMainLoop()
		self.system_bus = SystemBus(mainloop=dbus_ml)
		
		ecore.timer_add(5, self.init_dbus)

	def init_dbus(self):
		try:
			self.gsm = object_by_url('dbus:///org/pyneo/GsmDevice')
			self.wireless = object_by_url('dbus:///org/pyneo/gsmdevice/Network')
			self.keyring = object_by_url('dbus:///org/pyneo/GsmDevice')
		except Exception, e:
			print e
			#if not self.dbus_timer:
			#	self.dbus_timer = ecore.timer_add(2, self.init_dbus)
			# We had an error, keep the timer running
			#return True
		
		# No error, all went well
		#if self.dbus_timer: self.dbus_timer.stop()
		# D-Bus is ready, let's init GSM
		self.gsm_on()

	def gsm_on(self):
		try:
			if self.gsm.GetPower('sample', dbus_interface=DIN_POWERED, ):
				print '---', 'gsm device is already on'
			else:
				self.gsm.SetPower('sample', True, dbus_interface=DIN_POWERED, )
				print '---', 'switching device on'
		except Exception, e:
			print e
			#if not self.gsm_timer:
			#	self.gsm_timer = ecore.timer_add(5, self.gsm_on)
			# We had an error, keep the timer running
			#return True
		# No error
		#if self.gsm_timer: self.gsm_timer.stop()
		# GSM ready, let's ask SIM PIN
		self.sim_pin()

	def sim_pin(self):
		self.res = dedbusmap(self.keyring.GetOpened(dbus_interface=DIN_KEYRING))
		if self.res['code'] != 'READY':
			print '---', 'opening keyring'
			self.part_text_set("numberdisplay_text", "Enter " + self.res['code'])
			self.res = dedbusmap(self.keyring.GetOpened(dbus_interface=DIN_KEYRING))
		else:
			print '---', 'already authorized'
			self.nw_register()

	def nw_register(self):
		self.nw_res = dedbusmap(self.wireless.GetStatus(dbus_interface=DIN_WIRELESS))
		if not self.nw_res['stat'] in (1, 5, ):
			print '---', 'registering to gsm network'
			self.wireless.Register(dbus_interface=DIN_WIRELESS)
			self.nw_res = dedbusmap(self.wireless.GetStatus(dbus_interface=DIN_WIRELESS))
		else:
			self.part_text_set("numberdisplay_text", "please dial")
			print '---', 'already registered'

	@edje.decorators.signal_callback("dialer_send", "*")
	def on_edje_signal_numberkey_triggered(self, emission, source):
		if self.res['code'] != 'READY':
			if source in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#", "*", ):
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "backspace":
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "dial":
				print '---', 'send pin'
				self.keyring.Open(''.join(self.text), dbus_interface=DIN_KEYRING, )
				self.part_text_set("numberdisplay_text", "register ...")
				self.nw_register()
		else:
			if source in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#", "*", ):
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "backspace":
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "dial":
				print '---', 'dial number'
				self.part_text_set("numberdisplay_text", "calling ...")
				os.system('alsactl -f /usr/share/openmoko/scenarios/gsmhandset.state restore')
				name = self.wireless.Initiate(''.join(self.text), dbus_interface=DIN_VOICE_CALL_INITIATOR, timeout=200, )
				time.sleep(20)
				call = object_by_url(name)
				call.Hangup(dbus_interface=DIN_CALL)

class TestView(object):
	def __init__(self):
		edje.frametime_set(FRAMETIME)
		self.evas_canvas = EvasCanvas(FULLSCREEN, "x11-16")
		
		self.groups = {}
		self.groups[EDJE_GROUP_NAME] = MainScreen(self)
		self.evas_canvas.evas_obj.data[EDJE_GROUP_NAME] = self.groups[EDJE_GROUP_NAME]
		self.groups[EDJE_GROUP_NAME].show()
		self.groups[EDJE_GROUP_NAME].part_text_set("numberdisplay_text", "wait ...")

class EvasCanvas(object):
	def __init__(self, fullscreen, engine_name):
		if engine_name == "x11":
			engine = ecore.evas.SoftwareX11
#		elif engine_name == "x11-16":
#			if ecore.evas.engine_type_supported_get("software_x11_16"):
#				engine = ecore.evas.SoftwareX11_16
		else:
			print "warning: x11-16 is not supported, falling back to x11"
			engine = ecore.evas.SoftwareX11
		
		self.evas_obj = engine(w=WIDTH, h=HEIGHT)
		self.evas_obj.callback_delete_request = self.on_delete_request
		self.evas_obj.callback_resize = self.on_resize
		
		self.evas_obj.title = TITLE
		self.evas_obj.name_class = WM_INFO
		self.evas_obj.fullscreen = fullscreen
#		self.evas_obj.size = str(WIDTH) + 'x' + str(HEIGHT)
		self.evas_obj.show()

	def on_resize(self, evas_obj):
		x, y, w, h = evas_obj.evas.viewport
		size = (w, h)
		for key in evas_obj.data.keys():
			evas_obj.data[key].size = size

	def on_delete_request(self, evas_obj):
		ecore.main_loop_quit()

if __name__ == "__main__":
	TestView()
	ecore.main_loop_begin()

'''
export LDFLAGS="$LDFLAGS -L/opt/e17/lib"
export PKG_CONFIG_PATH="/opt/e17/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$PATH:/opt/e17/bin"
export PYTHONPATH="/home/fgau/usr/lib/python2.5/site-packages"

edje_cc -v -id ../images -fd ../fonts *edc
'''

