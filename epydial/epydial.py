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
APP_TITLE = "epydial"
WM_INFO = ("epydial", "epydial")

EDJE_FILE_PATH = "data/themes/default/"

MAIN_SCREEN_NAME = "pyneo/dialer/main"
INCALL_SCREEN_NAME = "pyneo/dialer/incall"

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
	def __init__(self, group_manager, group):
		
		# Theme file name is formed as follows:
		# Last two group name parts, combined by underscore
		# pyneo/dialer/main -> dialer_main.edj
		group_parts = group.split("/")
		file_name = EDJE_FILE_PATH + group_parts[-2] + "_" + group_parts[-1] + ".edj"
		
		if not os.path.exists(file_name):
			raise IOError("Edje theme file for group %s not found: %s" % (group, file_name))
		
		try:
			edje.Edje.__init__(self, group_manager.get_evas(), file=file_name, group=group)
		except edje.EdjeLoadError, e:
			raise SystemExit("Error loading %s: %s" % (file_name, e))
		
		self.size = group_manager.get_evas().size


class InCallScreen(EdjeGroup):
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, INCALL_SCREEN_NAME)

	def on_dbus_initialized(self):
		print "Dbus is ready, says InCallScreen"


class MainScreen(EdjeGroup):
	text = None
	
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, MAIN_SCREEN_NAME)
		self.text = []

	def on_dbus_initialized(self):
		print "Dbus is ready, says MainScreen"

	def on_sim_pin_required(self):
		print "SIM REQUIRED"

	def on_gsm_ready(self):
		print "GSM READY"

	@edje.decorators.signal_callback("dialer_send", "*")
	def on_edje_signal_numberkey_triggered(self, emission, source):
		if self.res['code'] != 'READY':
			if len(self.text) < 4 and source.isdigit():
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", '*' * len(self.text))
			elif source == "backspace":
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", '*' * len(self.text))
			elif source == "dial":
				print '---', 'send pin'
				self.part_text_set("numberdisplay_text", "register ...")
				self.keyring.Open(''.join(self.text), dbus_interface=DIN_KEYRING, )
				self.nw_register()
				self.res = dedbusmap(self.keyring.GetOpened(dbus_interface=DIN_KEYRING))
				self.part_text_set("numberdisplay_text", "please dial")
				self.text = []
		else:	
			if source.isdigit() or source in ('*', '#'):
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


class PyneoInterface(object):
	_dbus_timer = None
	_gsm_timer = None
	_init_callbacks = None
	_sim_pin_callback = None
	_gsm_ready_callback = None
	gsm = None
	gsm_net = None
	keyring = None

	@classmethod
	def register_init_callback(class_, callback):
		try:
			class_._init_callbacks.append(callback)
		except AttributeError:
			class_._init_callbacks = [callback]

	@classmethod
	def register_sim_pin_callback(class_, callback):
		class_._sim_pin_callback = callback

	@classmethod
	def register_gsm_ready_callback(class_, callback):
		class_._gsm_ready_callback = callback

	@classmethod
	def init(class_):
		try:
			class_.gsm = object_by_url('dbus:///org/pyneo/GsmDevice')
			class_.gsm_net = object_by_url('dbus:///org/pyneo/gsmdevice/Network')
			class_.keyring = object_by_url('dbus:///org/pyneo/GsmDevice')
		
		except Exception, e:
			print "XXXXXXX1 " + str(e)
			if not class_._dbus_timer:
				class_._dbus_timer = ecore.timer_add(5, class_.init)
			
			# We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error, all went well
		if class_._dbus_timer: class_._dbus_timer.stop()
		
		# Register our own D-Bus callbacks
		class_.gsm.connect_to_signal("Status", class_.on_gsm_net_status, dbus_interface=DIN_NETWORK)
		
		# Notify all screens that the interfaces are here so that they can connect their signal callbacks
		for callback in class_._init_callbacks:
			callback()
		
		# D-Bus is ready, let's power up GSM
		class_.power_up_gsm()

	@classmethod
	def power_up_gsm(class_):
		try:
			if class_.gsm.GetPower(APP_TITLE, dbus_interface=DIN_POWERED, ):
				print '---', 'gsm device is already on'
			else:
				class_.gsm.SetPower(APP_TITLE, True, dbus_interface=DIN_POWERED, )
				print '---', 'switching device on'
			
		except Exception, e:
			print "XXXXXXX2 " + str(e)
			if not class_._gsm_timer:
				class_._gsm_timer = ecore.timer_add(5, class_.power_up_gsm)
			 
			#We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error
		if class_._gsm_timer: class_._gsm_timer.stop()
		
		# Inquire status and act appropriately
		gsm_status = dedbusmap(class_.gsm_net.GetStatus(dbus_interface=DIN_WIRELESS))
		
		try:
			if gsm_status["stat"] == 0: class_._sim_pin_callback()
		except AttributeError:
			raise NotImplementedError("No one here to handle SIM PIN entry!")
		
		try:
			if gsm_status["stat"] in (1, 5): class_._gsm_ready_callback()
		except AttributeError:
			raise NotImplementedError("No one here to handle GSM ready status!")

	@classmethod
	def on_gsm_net_status(class_, status_map):
		status_map = dedbusmap(status_map)
		print "Status: " + str(status_map)


class Dialer(object):
	screens = None
	evas_canvas = None
	system_bus = None
	
	def __init__(self):
		# Initialize the GUI
		edje.frametime_set(FRAMETIME)
		self.evas_canvas = EvasCanvas(FULLSCREEN, "x11-16")
		
		self.screens = {}
		
		self.init_screen(MAIN_SCREEN_NAME, MainScreen(self))
		self.init_screen(INCALL_SCREEN_NAME, InCallScreen(self))
		
		self.screens[MAIN_SCREEN_NAME].part_text_set("numberdisplay_text", "wait ...")
		
		self.show_screen(MAIN_SCREEN_NAME)
		
		# Initialize the D-Bus interface to pyneo
		dbus_ml = e_dbus.DBusEcoreMainLoop()
		self.system_bus = SystemBus(mainloop=dbus_ml)
		PyneoInterface.init()


	def init_screen(self, screen_name, instance):
		self.screens[screen_name] = instance
		self.evas_canvas.evas_obj.data[screen_name] = instance
		
		# Attempt to register the screen's callbacks
		try:
			PyneoInterface.register_init_callback(instance.on_dbus_initialized)
		except AttributeError:
			pass
		
		try:
			PyneoInterface.register_sim_pin_callback(instance.on_sim_pin_required)
		except AttributeError:
			pass
		
		try:
			PyneoInterface.register_gsm_ready_callback(instance.on_gsm_ready)
		except AttributeError:
			pass


	def show_screen(self, screen_name):
		for (name, screen) in self.screens.items():
			if name == screen_name:
				screen.show()
			else:
				screen.hide()

	def get_evas(self):
		return self.evas_canvas.evas_obj.evas


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
		
		self.evas_obj.title = APP_TITLE
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
	Dialer()
	ecore.main_loop_begin()

'''
export LDFLAGS="$LDFLAGS -L/opt/e17/lib"
export PKG_CONFIG_PATH="/opt/e17/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$PATH:/opt/e17/bin"
export PYTHONPATH="/home/fgau/usr/lib/python2.5/site-packages"
'''

