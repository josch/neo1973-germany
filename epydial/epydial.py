#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

WIDTH = 480
HEIGHT = 640

FRAMETIME = 1.0 / 20
IMAGE_CACHE_SIZE = 6
FONT_CACHE_SIZE = 2

FULLSCREEN = True
APP_TITLE = "epydial"
WM_INFO = ("epydial", "epydial")

EDJE_FILE_PATH = "data/themes/blackwhite/"

DIALER_SCREEN_NAME = "pyneo/dialer/main"
INCALL_SCREEN_NAME = "pyneo/dialer/incall"
GSM_STATUS_SCREEN_NAME = "pyneo/gsm/status"
GPS_STATUS_SCREEN_NAME = "pyneo/gps/status"

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


class PyneoController(object):
	_dbus_timer = None
	_gsm_timer = None
	_keyring_timer = None
	_gps_timer = None
	_callbacks = {}
	_calls = {}
	
	gsm = None
	pwr = None
	gps = None
	gsm_wireless = None
	gsm_keyring = None
	
	gsm_wireless_status = None
	gsm_keyring_status = None
	
	call_type = None

	@classmethod
	def register_callback(class_, event_name, callback):
		print "In register_callback: ", event_name
		try:
			class_._callbacks[event_name].append(callback)
		
		except KeyError:
			# _callbacks[callback_name] undefined
			class_._callbacks[event_name] = [callback]

	@classmethod
	def notify_callbacks(class_, event_name, *args):
		try:
			for cb in class_._callbacks[event_name]:
				cb(*args)
		
		except KeyError:
			pass

	@classmethod
	def init(class_):
		try:
			class_.gsm = object_by_url('dbus:///org/pyneo/GsmDevice')
			class_.gsm_wireless = object_by_url(class_.gsm.GetDevice('wireless'))
			class_.pwr = object_by_url('dbus:///org/pyneo/Power')
			class_.gps = object_by_url('dbus:///org/pyneo/GpsLocation')
			class_.call_type = 'nix'
		
		except Exception, e:
			print "Pyneo error: " + str(e)
			if not class_._dbus_timer:
				class_._dbus_timer = ecore.timer_add(5, class_.init)
			
			# We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error (anymore)
		if class_._dbus_timer: class_._dbus_timer.stop()
		
		# Register our own D-Bus callbacks
		class_.gsm_wireless.connect_to_signal("Status", class_.on_gsm_wireless_status, dbus_interface=DIN_WIRELESS)
		class_.pwr.connect_to_signal("Status", class_.on_pwr_status, dbus_interface=DIN_POWERED)

	@classmethod
	def get_pwr_status(class_):
		status = class_.pwr.GetStatus(dbus_interface=DIN_POWERED)
		class_.on_pwr_status(status)

	@classmethod
	def power_status_gsm(class_):
		class_.notify_callbacks("power_status_gsm", class_.gsm.GetPower(APP_TITLE, dbus_interface=DIN_POWERED))

	@classmethod
	def power_up_gsm(class_):
		try:
			if class_.gsm.GetPower(APP_TITLE, dbus_interface=DIN_POWERED):
				print '---', 'gsm device is already on'
			else:
				class_.gsm.SetPower(APP_TITLE, True, dbus_interface=DIN_POWERED)
				print '---', 'switching gsm device on'
			
		except Exception, e:
			print "GSM error: " + str(e)
			if not class_._gsm_timer:
				class_._gsm_timer = ecore.timer_add(5, class_.power_up_gsm)
			 
			# We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error (anymore)
		if class_._gsm_timer: class_._gsm_timer.stop()

	@classmethod
	def get_gsm_keyring(class_):
		try:
			class_.gsm_keyring = object_by_url(class_.gsm_wireless.GetKeyring())
			
		except Exception, e:
			print "SIM error: " + str(e)
			if not class_._keyring_timer:
				class_._keyring_timer = ecore.timer_add(5, class_.get_gsm_keyring)
			 
			# We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error (anymore)
		if class_._keyring_timer: class_._keyring_timer.stop()
			
		class_.gsm_keyring.connect_to_signal("Opened", class_.on_gsm_keyring_status, dbus_interface=DIN_KEYRING)
			
		# Inquire SIM status and act accordingly to the initial state
		status = class_.gsm_keyring.GetOpened(dbus_interface=DIN_KEYRING)
		class_.on_gsm_keyring_status(status)
		
	@classmethod
	def gsm_sim_locked(class_):
		return class_.gsm_keyring_status['code'] != 'READY'

	@classmethod
	def gsm_unlock_sim(class_, key):
		class_.gsm_keyring.Open(key, dbus_interface=DIN_KEYRING)

	@classmethod
	def gsm_dial(class_, number):
		os.system('alsactl -f /usr/share/openmoko/scenarios/gsmhandset.state restore')
		
		name = class_.gsm_wireless.Initiate(number, dbus_interface=DIN_VOICE_CALL_INITIATOR, timeout=200)
		call = object_by_url(name)
		
		# Initialize "active call" counter
		class_._calls[call] = 1
		
#		class_.notify_callbacks("gsm_dialing")

	@classmethod
	def gsm_hangup(class_):
		# Find call with highest "active call" counter - it'll be the one currently active
		call = None
		highest = 0
		
		for (call_obj, counter) in class_._calls.items():
			if counter > highest:
				highest = counter
				call = call_obj
		
#		if call: 
		call.Hangup(dbus_interface=DIN_CALL)
		os.system('alsactl -f /usr/share/openmoko/scenarios/stereoout.state restore')
		class_.call_type = 'nix'

		# Remove the call from our list
#		class_._calls.__delitem__(call_obj)

	@classmethod
	def on_gsm_wireless_status(class_, status_map):
		status = dedbusmap(status_map)
		class_.gsm_net_status = status
		print "GSM NET Status: " + str(status)
		
		if status.has_key('stat'):
			nw_status = status['stat']
		
			if nw_status == 0:
				class_.notify_callbacks("gsm_unregistered")
			elif nw_status in (1, 5):
				class_.notify_callbacks("gsm_registered")
			elif nw_status == 2:
				class_.notify_callbacks("gsm_registering")
			elif nw_status == 3:
				class_.notify_callbacks("gsm_reg_denied")
			elif nw_status == 4:
				raise NotImplementedError("GSM registration has unknown state")
		
		if status.has_key('phone_activity_status'):
			ph_status = status['phone_activity_status']
			
			if ph_status == 0 and class_.call_type != 'outgoing':
#				class_.pwr.BlinkenLeds("power:blue", 0, 0, 0, dbus_interface=DIN_POWER)
				class_.notify_callbacks("gsm_phone_call_end")
			if ph_status == 3:
#				class_.pwr.BlinkenLeds("power:blue", 400, 1300, 0, dbus_interface=DIN_POWER)
				class_.notify_callbacks("gsm_phone_ringing")
			if ph_status == 4:
				class_.notify_callbacks("gsm_phone_call_start")
		
		if status.has_key('rssi'):
			class_.notify_callbacks("gsm_signal_strength_change", status['rssi'])
			
		if status.has_key('oper'):
			class_.notify_callbacks("gsm_operator_change", status['oper'])
			
		if status.has_key('number'):
			class_.notify_callbacks("gsm_number_display", status['number'])

	@classmethod
	def on_gsm_keyring_status(class_, status_map):
		status = dedbusmap(status_map)
		class_.gsm_keyring_status = status
		print "SIM Status: " + str(status)
		
		if status["code"] == "READY":
			class_.notify_callbacks("sim_ready")

			# Try registering on the network
			class_.gsm_wireless.Register(dbus_interface=DIN_WIRELESS)

		else:
			class_.notify_callbacks("sim_key_required", status["code"])

	@classmethod
	def power_status_gps(class_):
		class_.notify_callbacks("power_status_gps", class_.gps.GetPower(APP_TITLE, dbus_interface=DIN_POWERED))
		
	@classmethod
	def power_up_gps(class_):
		print 'power_up_gps'
		try:
			if class_.gps.GetPower(APP_TITLE, dbus_interface=DIN_POWERED):
				print '---', 'gps device is already on'
			else:
				class_.gps.SetPower(APP_TITLE, True, dbus_interface=DIN_POWERED)
				print '---', 'switching gps device on'
			
		except Exception, e:
			print "GPS error: " + str(e)
			if not class_._gps_timer:
				class_._gps_timer = ecore.timer_add(5, class_.power_up_gps)
			 
			# We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error (anymore)
		if class_._gps_timer: class_._gps_timer.stop()
		
		# Register our own D-Bus Gps callbacks
		class_.gps.connect_to_signal("Position", class_.on_gps_position_status, dbus_interface=DIN_LOCATION)
		
		class_.notify_callbacks("power_status_gps", class_.gps.GetPower(APP_TITLE, dbus_interface=DIN_POWERED))
		
		status = class_.gps.GetPosition(dbus_interface=DIN_LOCATION)
		class_.on_gps_position_status(status)

	@classmethod
	def power_down_gps(class_):
		class_.gps.SetPower(APP_TITLE, False, dbus_interface=DIN_POWERED)
		class_.notify_callbacks("power_status_gps", class_.gps.GetPower(APP_TITLE, dbus_interface=DIN_POWERED))

	@classmethod
	def on_gps_position_status(class_, status_map):
		status = dedbusmap(status_map)
		print "GPS Status: " + str(status)

		if status.has_key('fix'):
			class_.notify_callbacks("gps_position_change", status)

	@classmethod
	def on_pwr_status(class_, status_map):
		status = dedbusmap(status_map)
		print "POWER Status: " + str(status)
		class_.notify_callbacks("pwr_status_change", status)

	@classmethod
	def show_dialer_screen(class_):
		class_.notify_callbacks("show_dialer_screen")

	@classmethod
	def show_gsm_status_screen(class_):
		class_.notify_callbacks("show_gsm_status_screen")

	@classmethod
	def show_gps_status_screen(class_):
		class_.notify_callbacks("show_gps_status_screen")

	@classmethod
	def show_incall_screen(class_, calling_type):
		class_.call_type = calling_type
		print "CALLING_TYPE: ", class_.call_type
		class_.notify_callbacks("gsm_phone_call_start")


from dialer_screen import *
from incall_screen import *
from gsm_status_screen import *
from gps_status_screen import *


class Dialer(object):
	screens = None
	evas_canvas = None
	system_bus = None
	
	def __init__(self):
		# Initialize the GUI
		edje.frametime_set(FRAMETIME)
		self.evas_canvas = EvasCanvas(FULLSCREEN, "x11-16")
		
		self.screens = {}

		# Register our own callbacks
		PyneoController.register_callback("gsm_phone_ringing", self.on_ringing)
		PyneoController.register_callback("gsm_phone_call_start", self.on_call_start)
		PyneoController.register_callback("gsm_phone_call_end", self.on_call_end)
		PyneoController.register_callback("show_gsm_status_screen", self.on_gsm_status_screen)
		PyneoController.register_callback("show_gps_status_screen", self.on_gps_status_screen)
		PyneoController.register_callback("show_dialer_screen", self.on_call_end)
		
		# Initialize the D-Bus interface to pyneo
		dbus_ml = e_dbus.DBusEcoreMainLoop()
		self.system_bus = SystemBus(mainloop=dbus_ml)
		PyneoController.init()

		self.init_screen(DIALER_SCREEN_NAME, DialerScreen(self))
		PyneoController.show_dialer_screen()
#		self.show_screen(DIALER_SCREEN_NAME)
		self.init_screen(INCALL_SCREEN_NAME, InCallScreen(self))
		self.init_screen(GSM_STATUS_SCREEN_NAME, GsmStatusScreen(self))
		self.init_screen(GPS_STATUS_SCREEN_NAME, GpsStatusScreen(self))

		PyneoController.power_up_gsm()
		PyneoController.get_gsm_keyring()

	def init_screen(self, screen_name, instance):
		self.screens[screen_name] = instance
		self.evas_canvas.evas_obj.data[screen_name] = instance
		
		# Attempt to register the screen default callbacks
		try:
			instance.register_pyneo_callbacks()
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

	def on_ringing(self):
		self.show_screen(INCALL_SCREEN_NAME)

	def on_call_start(self):
		self.show_screen(INCALL_SCREEN_NAME)

	def on_call_end(self):
		self.show_screen(DIALER_SCREEN_NAME)

	def on_gsm_status_screen(self):
		self.show_screen(GSM_STATUS_SCREEN_NAME)

	def on_gps_status_screen(self):
		self.show_screen(GPS_STATUS_SCREEN_NAME)


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
		self.evas_obj.evas.image_cache_set(IMAGE_CACHE_SIZE*1024*1024)
		self.evas_obj.evas.font_cache_set(FONT_CACHE_SIZE*1024*1024)
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

