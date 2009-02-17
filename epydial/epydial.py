#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
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
PIX_FILE_PATH = "/media/card/hon/"
TRACK_FILE_PATH = "/media/card/track/"
DB_FILE_PATH = "/media/card/epydialdb/epydial.sqlite"
DB_PATH = "/media/card/epydialdb/"
PIX_WEATHER_FILE_PATH = "data/themes_data/blackwhite/images/stardock_weather/"
MP3_FILE_PATH = "/media/card/mp3/"
COVER_FILE_PATH = "/media/card/epydial/cover/"
RINGTONE_FILE = "/usr/share/epydial/data/sounds/ring-ring.mp3"

DIALER_SCREEN_NAME = "pyneo/dialer/main"
INCALL_SCREEN_NAME = "pyneo/dialer/incall"
GSM_STATUS_SCREEN_NAME = "pyneo/gsm/status"
GPS_STATUS_SCREEN_NAME = "pyneo/gps/status"
HON_SCREEN_NAME = "pyneo/hon/screen"
CALC_SCREEN_NAME = "pyneo/calc/screen"
PIX_SCREEN_NAME = "pyneo/pix/screen"
CONTACTS_SCREEN_NAME = "pyneo/contacts/screen"
SMS_SCREEN_NAME = "pyneo/sms/screen"
SMS_DETAIL_SCREEN_NAME = "pyneo/sms/detail"
WEATHER_SCREEN_NAME = "pyneo/weather/screen"
AUDIO_SCREEN_NAME = "pyneo/audio/screen"

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
from time import sleep

from pyneo.dbus_support import *
from pyneo.sys_support import pr_set_name

from ConfigParser import SafeConfigParser
from sqlite3 import connect

#import cairo

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
	hon = None
	mp3 = None
	mp3_music = None
	gsm_wireless = None
	gsm_keyring = None
	gsm_sms = None
	hon_hotornot = None
	
	gsm_wireless_status = None
	gsm_keyring_status = None
	
	call_type = None
	
	brightness_value = None

	call = None
	callsigs = []

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
			class_.gsm_wireless = object_by_url(class_.gsm.GetDevice('wireless', dbus_interface=DIN_POWERED))
			class_.gsm_sms = object_by_url(class_.gsm.GetDevice('shortmessage_storage', dbus_interface=DIN_POWERED))
			class_.pwr = object_by_url('dbus:///org/pyneo/Power')
			class_.gps = object_by_url('dbus:///org/pyneo/GpsLocation')
			class_.hon = object_by_url('dbus:///org/pyneo/HotOrNot')
			class_.hon_hotornot = object_by_url(class_.hon.GetDevice('hotornot', dbus_interface=DIN_POWERED))
			class_.mp3 = object_by_url('dbus:///org/pyneo/Player')
			class_.call_type = 'nix'
			class_.brightness_value = 60
			class_.call = None
			class_.callsigs = []
		
		except Exception, e:
			print "Pyneo error: " + str(e)
			if not class_._dbus_timer:
				class_._dbus_timer = ecore.timer_add(5, class_.init)
			
			# We had an error, keep the timer running if we were called by ecore
			return True
		
		# No error (anymore)
		if class_._dbus_timer: class_._dbus_timer.stop()
		
		# Register our own D-Bus callbacks (device status, new calls, power status, new sms, new music title)
		class_.gsm_wireless.connect_to_signal('Status', class_.on_gsm_wireless_status, dbus_interface=DIN_WIRELESS)
		class_.gsm_wireless.connect_to_signal('New', class_.check_new_call, dbus_interface=DIN_WIRELESS)
		class_.pwr.connect_to_signal('Status', class_.on_pwr_status, dbus_interface=DIN_POWERED)
		class_.gsm_sms.connect_to_signal('New', class_.check_new_sms, dbus_interface=DIN_STORAGE)
		class_.mp3.connect_to_signal('Status', class_.on_mp3_status, dbus_interface='org.pyneo.Music')

	@classmethod
	def get_pwr_status(class_):
		status = class_.pwr.GetStatus(dbus_interface=DIN_POWERED)
		class_.on_pwr_status(status)

	@classmethod
	def get_device_status(class_):
		class_.notify_callbacks("device_status", class_.gsm.GetStatus(dbus_interface=DIN_POWERED))

	@classmethod
	def power_status_gsm(class_):
		class_.notify_callbacks("power_status_gsm", class_.gsm.GetPower(APP_TITLE, dbus_interface=DIN_POWERED))

	@classmethod
	def get_hon(class_):
		class_.notify_callbacks("get_hon", class_.hon_hotornot.GetHotOrNot(dbus_interface=DIN_HOTORNOT))

	@classmethod
	def vote_hon(class_, vote):
		class_.hon_hotornot.HotOrNot(vote, dbus_interface=DIN_HOTORNOT)

	@classmethod
	def show_sms_detail(class_, number, status):
		class_.notify_callbacks("show_sms_detail", number, status)

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
			class_.gsm_keyring = object_by_url(class_.gsm_wireless.GetKeyring(dbus_interface=DIN_AUTHORIZED))
			
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
		class_.notify_callbacks("gsm_phone_call_start")
		name = class_.gsm_wireless.Initiate(number, dbus_interface=DIN_VOICE_CALL_INITIATOR, timeout=200)
		class_.call = object_by_url(name)

	@classmethod
	def gsm_hangup(class_):
		os.system('alsactl -f /usr/share/openmoko/scenarios/stereoout.state restore')
		class_.call_type = 'nix'
		class_.call = object_by_url('dbus:///org/pyneo/gsmdevice/Call/1')
		class_.call.Hangup(dbus_interface=DIN_CALL)

	@classmethod
	def gsm_accept(class_):
		os.system('alsactl -f /usr/share/openmoko/scenarios/gsmhandset.state restore')
		class_.call.Accept(dbus_interface=DIN_CALL)

	@classmethod
	def gsm_details(class_):
		class_.notify_callbacks("gsm_details", class_.gsm_wireless.GetStatus(dbus_interface=DIN_WIRELESS))

	@classmethod
	def on_gsm_wireless_status(class_, status_map):
		status = dedbusmap(status_map)
		class_.gsm_net_status = status
		print 'GSM NET Status: %s'%status
		
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
	
		if status.has_key('rssi'):
			class_.notify_callbacks("gsm_signal_strength_change", status['rssi'])
			
		if status.has_key('oper'):
			class_.first_check_new_sms()
			class_.notify_callbacks("gsm_operator_change", status['oper'])
			
		if status.has_key('number'):
			class_.notify_callbacks("gsm_number_display", status['number'])

		class_.notify_callbacks("gsm_details", status)

	@classmethod
	def on_gsm_keyring_status(class_, status_map):
		status = dedbusmap(status_map)
		class_.gsm_keyring_status = status
		print "SIM Status: " + str(status)
		
		if status["code"] == "READY":
			class_.notify_callbacks("sim_ready")

			# Try registering on the network
			res = dedbusmap(class_.gsm_wireless.GetStatus(dbus_interface=DIN_WIRELESS, ))
			if not res['stat'] in (1, 5, ):
				print '---', 'registering to gsm network'
				class_.gsm_wireless.Register(dbus_interface=DIN_WIRELESS)
				res = dedbusmap(class_.gsm_wireless.GetStatus(dbus_interface=DIN_WIRELESS, ))
			else:
				print '---', 'already registered'
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
		class_.notify_callbacks("capacity_change", status)
		class_.notify_callbacks("pwr_status_change", status)

	@classmethod
	def show_dialer_screen(class_):
		class_.pwr.SetBrightness(class_.brightness_value, dbus_interface=DIN_POWER)
		class_.pwr.GetStatus(dbus_interface=DIN_POWERED)
		class_.notify_callbacks("show_dialer_screen")

	@classmethod
	def show_gsm_status_screen(class_):
		class_.notify_callbacks("show_gsm_status_screen")
		class_.notify_callbacks("brightness_change", class_.brightness_value)

	@classmethod
	def show_gps_status_screen(class_):
		class_.notify_callbacks("show_gps_status_screen")

	@classmethod
	def show_incall_screen(class_, calling_type):
		class_.call_type = calling_type
		print "CALLING_TYPE: ", class_.call_type
		class_.notify_callbacks("gsm_phone_call_start")

	@classmethod
	def show_hon_screen(class_):
		class_.notify_callbacks("show_hon_screen")

	@classmethod
	def show_calc_screen(class_):
		class_.notify_callbacks("show_calc_screen")

	@classmethod
	def show_pix_screen(class_):
		class_.notify_callbacks("show_pix_screen")

	@classmethod
	def brightness_change(class_, up_down):
		if up_down == 'button_right_bg_brightness':
			class_.brightness_value += 10
			if class_.brightness_value > 100: class_.brightness_value = 100
		else:
			class_.brightness_value -= 10
			if class_.brightness_value < 0: class_.brightness_value = 0
		class_.pwr.SetBrightness(class_.brightness_value, dbus_interface=DIN_POWER)
		class_.notify_callbacks("brightness_change", class_.brightness_value)

	@classmethod
	def scan_operator(class_):
		class_.notify_callbacks("scan_operator", dedbusmap(class_.gsm_wireless.Scan(timeout=100.0, dbus_interface=DIN_WIRELESS, )))

	@classmethod
	def show_contacts_screen(class_):
		class_.notify_callbacks("show_contacts_screen")

	@classmethod
	def check_new_call(class_, newmap):
		def CallStatus(newmap):
			newmap = dedbusmap(newmap)
			print '---', 'CallStatus'

		def CallRing(newmap):
			newmap = dedbusmap(newmap)
			class_.notify_callbacks("gsm_phone_ringing")
			if newmap['number']: class_.notify_callbacks("gsm_number_display", newmap['number'])
			print '---', 'CallRing'

		def CallEnd(newmap):
			class_.mp3.StopRingtone(dbus_interface='org.pyneo.Music')
			class_.notify_callbacks("gsm_phone_call_end")
			os.system('alsactl -f /usr/share/openmoko/scenarios/stereoout.state restore')
			newmap = dedbusmap(newmap)
			print '---', 'CallEnd'
			if class_.call:
				class_.call = None
				while class_.callsigs:
					class_.callsigs.pop().remove()

		newmap = dedbusmap(newmap)
		print '---', 'CallNew'
		class_.mp3.PlayRingtone(dbus_interface='org.pyneo.Music')
		for n, v in newmap.items():
#			print '\t', n, ':', v
			class_.call = object_by_url(n)
			class_.callsigs.append(class_.call.connect_to_signal('Ring', CallRing, dbus_interface=DIN_CALL, ))
			class_.callsigs.append(class_.call.connect_to_signal('Status', CallStatus, dbus_interface=DIN_CALL, ))
			class_.callsigs.append(class_.call.connect_to_signal('End', CallEnd, dbus_interface=DIN_CALL, ))

	@classmethod
	def on_mp3_status(class_, newmap):
		newmap = dedbusmap(newmap)
		print 'Music MP3 Status: %s' %newmap
		class_.notify_callbacks("on_get_mp3_tags", newmap)

	@classmethod
	def insert_new_sms(class_, status, from_msisdn, time, text):
		connection = connect(DB_FILE_PATH)
		cursor = connection.cursor()
		cursor.execute('INSERT INTO sms (status, from_msisdn, time, sms_text) VALUES (?, ?, ?, ?)', (status, from_msisdn, time, text,))
		connection.commit()

	@classmethod
	def check_new_sms(class_, newmap,):
		res = dedbusmap(newmap)
		for n in res:
			sm = object_by_url(n)
			content = dedbusmap(sm.GetContent(dbus_interface=DIN_ENTRY))
			PyneoController.insert_new_sms('REC UNREAD', content['from_msisdn'], content['time'], content['text'].encode('utf-8'))
			print '--- NEW SMS:', content['from_msisdn'], content['time'], content['text'].encode('utf-8')
		class_.gsm_sms.DeleteAll(dbus_interface=DIN_STORAGE)

	@classmethod
	def first_check_new_sms(class_):
		try:
			res = class_.gsm_sms.ListAll(dbus_interface=DIN_STORAGE)
			for n in res:
				sm = object_by_url(n)
				content = dedbusmap(sm.GetContent(dbus_interface=DIN_ENTRY))
				PyneoController.insert_new_sms('REC UNREAD', content['from_msisdn'], content['time'], content['text'].encode('utf-8'))
		except:
			print '--- NULL new sms'
		class_.gsm_sms.DeleteAll(dbus_interface=DIN_STORAGE)

	@classmethod
	def show_sms_screen(class_):
		class_.notify_callbacks("show_sms_screen")

	@classmethod
	def show_sms_screen_detail(class_):
		class_.notify_callbacks("show_sms_screen_detail")

	@classmethod
	def show_weather_screen(class_):
		class_.notify_callbacks("show_weather_screen")

	@classmethod
	def vibrate_start(class_):
		class_.pwr.Vibrate(10, 3, 1, dbus_interface=DIN_POWER)

	@classmethod
	def vibrate_stop(class_):
		class_.pwr.Vibrate(0, 0, 0, dbus_interface=DIN_POWER)

	@classmethod
	def show_audio_screen(class_):
		class_.notify_callbacks("show_audio_screen")

	@classmethod
	def play_music(class_):
		class_.mp3.Play(dbus_interface='org.pyneo.Music')

	@classmethod
	def stop_music(class_):
		class_.mp3.Stop(dbus_interface='org.pyneo.Music')

	@classmethod
	def pause_music(class_):
		class_.mp3.Pause(dbus_interface='org.pyneo.Music')

	@classmethod
	def next_music(class_):
		class_.mp3.Next(dbus_interface='org.pyneo.Music')

	@classmethod
	def previous_music(class_):
		class_.mp3.Previous(dbus_interface='org.pyneo.Music')

	@classmethod
	def set_playlist_from_dir(class_):
		class_.mp3.SetPlaylistFromDir(MP3_FILE_PATH, dbus_interface='org.pyneo.Music')

	@classmethod
	def get_mp3_tags(class_):
		class_.notify_callbacks("on_get_mp3_tags", class_.mp3.GetStatus(dbus_interface='org.pyneo.Music'))

	@classmethod
	def set_volume(class_, status):
		class_.mp3.SetVolume(status, dbus_interface='org.pyneo.Music')

	@classmethod
	def set_ringtone(class_, sound_file):
		class_.mp3.SetRingtone(sound_file, dbus_interface='org.pyneo.Music')

	@classmethod
	def set_ringtone_volume(class_, status):
		class_.mp3.SetRingtoneVolume(status, dbus_interface='org.pyneo.Music')

	@classmethod
	def play_ringtone(class_):
		class_.mp3.PlayRingtone(dbus_interface='org.pyneo.Music')

	@classmethod
	def stop_ringtone(class_):
		class_.mp3.StopRingtone(dbus_interface='org.pyneo.Music')

	@classmethod
	def get_song_duration(class_):
		class_.notify_callbacks('on_get_song_duration', class_.mp3.GetSongDuration(dbus_interface='org.pyneo.Music'))

	@classmethod
	def get_song_position(class_):
		class_.notify_callbacks('on_get_song_position', class_.mp3.GetSongPosition(dbus_interface='org.pyneo.Music'))

	@classmethod
	def db_check(class_):
		if not os.path.exists(DB_FILE_PATH):
			os.mkdir(DB_PATH)
			os.system('cp %s %s' % ('./data/db/epydial.sqlite', DB_PATH))
			print '--- Add db path and a empty sqlite db' 

from dialer_screen import *
from incall_screen import *
from gsm_status_screen import *
from gps_status_screen import *
from hon_screen import *
from calc_screen import *	
from pix_screen import *
from contacts_screen import *
from sms_screen import *
from sms_detail import *
from weather_screen import *
from audio_screen import *

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
		PyneoController.register_callback("show_hon_screen", self.on_hon_screen)
		PyneoController.register_callback("show_calc_screen", self.on_calc_screen)
		PyneoController.register_callback("show_pix_screen", self.on_pix_screen)
		PyneoController.register_callback("show_contacts_screen", self.on_contacts_screen)
		PyneoController.register_callback("show_sms_screen", self.on_sms_screen)
		PyneoController.register_callback("show_sms_screen_detail", self.on_sms_screen_detail)
		PyneoController.register_callback("show_weather_screen", self.on_weather_screen)
		PyneoController.register_callback("show_audio_screen", self.on_audio_screen)

		# Initialize the D-Bus interface to pyneo
		dbus_ml = e_dbus.DBusEcoreMainLoop()
		self.system_bus = SystemBus(mainloop=dbus_ml)
		PyneoController.init()

		self.init_screen(DIALER_SCREEN_NAME, DialerScreen(self))
		PyneoController.show_dialer_screen()
		self.init_screen(INCALL_SCREEN_NAME, InCallScreen(self))
		self.init_screen(GSM_STATUS_SCREEN_NAME, GsmStatusScreen(self))
		self.init_screen(GPS_STATUS_SCREEN_NAME, GpsStatusScreen(self))

		PyneoController.db_check()
		PyneoController.set_playlist_from_dir()
		PyneoController.set_ringtone(RINGTONE_FILE)
		PyneoController.set_ringtone_volume(0.6)
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

	def on_hon_screen(self):
		self.init_screen(HON_SCREEN_NAME, HonScreen(self))
		self.show_screen(HON_SCREEN_NAME)

	def on_calc_screen(self):
		self.init_screen(CALC_SCREEN_NAME, CalcScreen(self))
		self.show_screen(CALC_SCREEN_NAME)

	def on_pix_screen(self):
		self.init_screen(PIX_SCREEN_NAME, PixScreen(self))
		self.show_screen(PIX_SCREEN_NAME)

	def on_contacts_screen(self):
		self.init_screen(CONTACTS_SCREEN_NAME, ContactsScreen(self))
		self.show_screen(CONTACTS_SCREEN_NAME)

	def on_sms_screen(self):
		self.init_screen(SMS_SCREEN_NAME, SmsScreen(self))
		self.show_screen(SMS_SCREEN_NAME)

	def on_sms_screen_detail(self):
		self.init_screen(SMS_DETAIL_SCREEN_NAME, SmsDetail(self))
		self.show_screen(SMS_DETAIL_SCREEN_NAME)

	def on_weather_screen(self):
		self.init_screen(WEATHER_SCREEN_NAME, WeatherScreen(self))
		self.show_screen(WEATHER_SCREEN_NAME)

	def on_audio_screen(self):
		self.init_screen(AUDIO_SCREEN_NAME, AudioScreen(self))
		self.show_screen(AUDIO_SCREEN_NAME)

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

