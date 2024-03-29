#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = "Soeren Apel (abraxa@dar-clan.de), Frank Gau (fgau@gau-net.de), Thomas Gstaedtner (thomas (a) gstaedtner (.) net)"
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

from epydial import *

class DialerScreen(EdjeGroup):
	text = None

	def __init__(self, screen_manager):
		EdjeGroup.__init__(self, screen_manager, DIALER_SCREEN_NAME)
		self.text = []
		self.look_screen = False
		ecore.timer_add(60.0, self.display_time)
		self.display_time()
		
		self.part_text_set("numberdisplay_text", "Wait ...")

	def register_pyneo_callbacks(self):
		PyneoController.register_callback("sim_key_required", self.on_sim_key_required)
		PyneoController.register_callback("sim_ready", self.on_sim_ready)
		PyneoController.register_callback("gsm_registering", self.on_gsm_registering)
		PyneoController.register_callback("gsm_registered", self.on_gsm_registered)
		PyneoController.register_callback("gsm_operator_change", self.on_gsm_operator_change)
		PyneoController.register_callback("gsm_signal_strength_change", self.on_gsm_signal_strength_change)
		PyneoController.register_callback("capacity_change", self.on_capacity_change)

	def on_capacity_change(self, status):
		if status['status'] != "Charging":
			EdjeGroup.color_class_set(self, "battvolt_active", 255, 255, 255, 64, 0, 0, 0, 0, 0, 0, 0, 0)
		else:
			EdjeGroup.color_class_set(self, "battvolt_active", 255, 255, 255, 128, 0, 0, 0, 0, 0, 0, 0, 0)
		self.part_text_set("battvolt_text", "%s%%" % status['capacity'])
		
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

#	def on_gsm_dialing(self):
#		print '---', 'dial number'
#		self.part_text_set("numberdisplay_text", "Dialing ...")
		
	def on_gsm_operator_change(self, operator):
		self.part_text_set("operater_text", operator)
		
	def on_gsm_signal_strength_change(self, rssi):
		self.part_text_set("signalq_text", "%s dBm /"%str(rssi))
		
	def display_time(self):
		self.part_text_set("time_text", datetime.now().strftime('%H:%M'))
		return True


	@edje.decorators.signal_callback("dialer_send", "*")
	def on_edje_signal_numberkey_triggered(self, emission, source):
		if PyneoController.gsm_sim_locked():
			if source.isdigit():
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", '*' * len(self.text))
			elif source == "backspace":
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", '*' * len(self.text))
			elif source == "clear":
				self.text = []
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "dial":
				print '---', 'send pin'
				self.part_text_set("numberdisplay_text", "Verifying ...")
				PyneoController.gsm_unlock_sim(''.join(self.text))
		else:
			if self.look_screen:
				self.part_text_set("numberdisplay_text", "Screen locked")
				if source == "screen_locked":
					self.text = []
					self.look_screen = False
					self.part_text_set("numberdisplay_text", "Dial when ready")
			else:
				if source.isdigit() or source in ('*', '#'):
					self.text.append(source)
					print ''.join(self.text)
					self.part_text_set("numberdisplay_text", "".join(self.text))
				elif source == "backspace":
					self.text = self.text[:-1]
					print ''.join(self.text)
					self.part_text_set("numberdisplay_text", "".join(self.text))
				elif source == "clear":
					self.text = []
					print ''.join(self.text)
					self.part_text_set("numberdisplay_text", "".join(self.text))
				elif source == "screen_locked":
					self.text = []
					self.look_screen = True
					self.part_text_set("numberdisplay_text", "Screen locked")
				elif source == "dial" and ''.join(self.text) == "1":
					print '--- Gsm Status'
					self.text = []
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.power_status_gsm()
					PyneoController.get_device_status()
					PyneoController.show_gsm_status_screen()
				elif source == "dial" and ''.join(self.text) == "2":
					print '--- Gps Status'
					self.text = []
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.power_status_gps()
					PyneoController.show_gps_status_screen()
				elif source == "dial" and ''.join(self.text) == "3":
					print '--- Calculator'
					self.text =[]
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.show_calc_screen()
				elif source == "dial" and ''.join(self.text) == "4":
					print '--- Pix'
					self.text =[]
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.show_pix_screen()
				elif source == "dial" and ''.join(self.text) == "5":
					print '--- Yahoo Weather Screen'
					self.text = []
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.show_weather_screen()
				elif source == "dial" and ''.join(self.text) == "6":
					print '--- Hon Screen'
					self.text = []
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.show_hon_screen()
				elif source == "dial" and ''.join(self.text) == "7":
					print '--- Contacts Screen'
					self.text = []
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.show_contacts_screen()
				elif source == "dial" and ''.join(self.text) == "8":
					print '--- Sms Screen'
					self.text = []
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.show_sms_screen()
				elif source == "dial" and ''.join(self.text) == "9":
					print '--- Audio Screen'
					self.text = []
					self.part_text_set("numberdisplay_text", "".join(self.text))
					PyneoController.show_audio_screen()
				elif source == "dial":
					PyneoController.show_incall_screen('outgoing')
					PyneoController.gsm_dial("".join(self.text))

