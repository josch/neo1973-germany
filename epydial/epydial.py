#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), fgau, Thomas Gstaedner (thomas (a) gstaedtner (.) net)"
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

	def register_pyneo_callbacks(self):
		pass
		
	@edje.decorators.signal_callback("dialer_incall_send", "*")
	def on_edje_signal_dialer_incall_triggered(self, emission, source):
		if source == "Hangup Call":
			print source
			PyneoController.gsm_hangup()
		if source == "Accept Call":
			print source


class MainScreen(EdjeGroup):
	text = None
	TIMEOUT = 2.0
	
	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, MAIN_SCREEN_NAME)
		self.text = []
		self.last = 0.0
		ecore.timer_add(60.0, self.display_time)
		self.display_time()

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("sim_key_required", self.on_sim_key_required)
		PyneoController.register_callback("sim_ready", self.on_sim_ready)
		PyneoController.register_callback("gsm_registering", self.on_gsm_registering)
		PyneoController.register_callback("gsm_registered", self.on_gsm_registered)
		PyneoController.register_callback("gsm_dialing", self.on_gsm_dialing)
		PyneoController.register_callback("gsm_operator_change", self.on_gsm_operator_change)
		PyneoController.register_callback("gsm_signal_strength_change", self.on_gsm_signal_strength_change)
		
	def on_sim_key_required(self, key_type):
		print '---', 'opening keyring'
		self.part_text_set("numberdisplay_text", "Enter " + key_type)

	def on_sim_ready(self):
		print '---', 'SIM unlocked'
		self.part_text_set("numberdisplay_text", "SIM unlocked")
		self.text = []

	def on_gsm_registering(self):
		self.part_text_set("numberdisplay_text", "Registering ...")

	def on_gsm_registered(self):
		self.part_text_set("numberdisplay_text", "Dial when ready")

	def on_gsm_dialing(self):
		print '---', 'dial number'
		self.part_text_set("numberdisplay_text", "Dialing ...")
		
	def on_gsm_operator_change(self, operator):
		self.part_text_set("operater_text", operator)
		
	def on_gsm_signal_strength_change(self, rssi):
		self.part_text_set("signalq_text", "%s dBm"%str(rssi))
		
	def display_time(self):
		self.part_text_set("time_text", time.strftime("%H:%M", time.localtime()));
		return True;

	@edje.decorators.signal_callback("dialer_send", "*")
	def on_edje_signal_numberkey_triggered(self, emission, source):
		if PyneoController.gsm_sim_locked():
			if len(self.text) < 4 and source.isdigit():
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", '*' * len(self.text))
			elif source == "backspace_down":
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", '*' * len(self.text))
			elif source == "dial":
				print '---', 'send pin'
				self.part_text_set("numberdisplay_text", "Verifying ...")
				PyneoController.gsm_unlock_sim(''.join(self.text))
		else:
			if source.isdigit() or source in ('*', '#'):
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "backspace_down":
				time.time()-self.last < self.TIMEOUT
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "backspace_up" and time.time()-self.last > self.TIMEOUT:
				self.text = []
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "dial":
				PyneoController.gsm_dial("".join(self.text))
		self.last = time.time()


class PyneoController(object):
	_dbus_timer = None
	_gsm_timer = None
	_keyring_timer = None
	_callbacks = {}
	_calls = {}
	
	gsm = None
	gsm_wireless = None
	gsm_keyring = None
	
	gsm_wireless_status = None
	gsm_keyring_status = None

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
		
		# D-Bus is ready, let's power up GSM
		class_.power_up_gsm()

	@classmethod
	def power_up_gsm(class_):
		try:
			if class_.gsm.GetPower(APP_TITLE, dbus_interface=DIN_POWERED):
				print '---', 'gsm device is already on'
			else:
				class_.gsm.SetPower(APP_TITLE, True, dbus_interface=DIN_POWERED)
				print '---', 'switching device on'
			
		except Exception, e:
			print "GSM error: " + str(e)
			if not class_._gsm_timer:
				class_._gsm_timer = ecore.timer_add(5, class_.power_up_gsm)
			 
			# We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error (anymore)
		if class_._gsm_timer: class_._gsm_timer.stop()
		
		# Now we can request the keyring object for the SIM, it didn't exist before powering up
		class_.get_gsm_keyring()

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
		
		class_.notify_callbacks("gsm_dialing")

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
			
			if ph_status == 0:
				class_.notify_callbacks("gsm_phone_call_end")
			if ph_status == 3:
				class_.notify_callbacks("gsm_phone_ringing")
			if ph_status == 4:
				class_.notify_callbacks("gsm_phone_call_start")
		
		if status.has_key('rssi'):
			class_.notify_callbacks("gsm_signal_strength_change", status['rssi'])
			
		if status.has_key('oper'):
			class_.notify_callbacks("gsm_operator_change", status['oper'])

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
		PyneoController.init()
		
		# Register our own callbacks
		PyneoController.register_callback("gsm_phone_ringing", self.on_ringing)
		PyneoController.register_callback("gsm_phone_call_start", self.on_call_start)
		PyneoController.register_callback("gsm_phone_call_end", self.on_call_end)

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
		self.show_screen(MAIN_SCREEN_NAME)


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

