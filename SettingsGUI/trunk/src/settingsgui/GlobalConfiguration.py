"""
 * GlobalConfiguration.py - SettingsGUI - 
 *   Settings and default config files
 *
 * (C) 2007 by Kristian Mueller <kristian-m@kristian-m.de>
 * All Rights Reserved
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

NOTEBK_PADDING = 6
GSM_Panel_Instance = None

## used in Screen Panel
SYSFS_ENTRY_BACKLIGHT_BRIGHTNESS = "/sys/class/backlight/gta01-bl/brightness"
SYSFS_ENTRY_BACKLIGHT_POWER = "/sys/class/backlight/gta01-bl/power" # reverse

## used in Bluetooth Panel
SYSFS_ENTRY_BLUETOOTH_POWER = "/sys/bus/platform/devices/gta01-pm-bt.0/power_on"
HCICONFIG_CMD = "hciconfig"             ## using $PATH
#HCICONFIG_CMD = "/sbin/hciconfig"      ## openembedded
#HCICONFIG_CMD = "/usr/sbin/hciconfig"  ## ubuntu
HCITOOL_CMD = "hcitool"             ## using $PATH
BLUETOOTH_DEVICE = "hci0"

## used in Audio Panel
ALSA_STATES_DIR = "/etc/"

ALSA_ENTRYS = {
    "GSM Handset" : "gsmhandset.state", 
    "GSM Headset" : "gsmheadset.state", 
    "Capture Handset" : "capturehandset.state", 
    "Capture Headset" : "captureheadset.state", 
    "GSM Bluetooth" : "gsmbluetooth.state", 
    "Stereoout" : "stereoout.state"
}

ALSA_AMIXER = "/usr/bin/amixer"
## amixer cset numid=87 30

ALSA_CHANNEL_LEFT = 86
ALSA_CHANNEL_RIGHT = 87
ALSA_CHANNEL_MONO = 88


## PPP Settings and config files

DEFAULT_NAMESERVER = "208.67.222.222"     # from the OpenDNS project (2007-09-05)

PPP_PATH_TO_PPP = "/etc/ppp/"
PPP_PATH_TO_GLOBAL_PEERS = "/etc/ppp/peers/"
## ToDo move to ~/.settings-gui/ppp/ 
## => ToDo find out how to tell pppd...
PPP_PATH_TO_USER_PEERS = "/etc/ppp/peers/"   
PPP_GENCONFIG_NAME = "latest_gprs"
PPP_DEFAULT_CONFIG_NAME = "gprs"
PPP_INIT = "/usr/sbin/pppd"

PPP_SECRETS_FILES = ["/etc/ppp/pap-secrets", "/etc/ppp/chap-secrets"]

## from http://wiki.openmoko.org/wiki/Manually_using_GPRS 
## thanks Pavel!
PPP_DEFAULT_CONNECT_SCRIPT = """exec chat
    TIMEOUT         22
    ECHO            ON
    ABORT           '\\nBUSY\\r'
    ABORT           '\\nERROR\\r'
    ABORT           '\\nNO ANSWER\\r'
    ABORT           '\\nNO CARRIER\\r'
    ABORT           '\\nNO DIALTONE\\r'
    ABORT           '\\nRINGING\\r\\n\\r\\nRINGING\\r'
    SAY             "\\nDefining Packet Data Protocol context...\\n"
    ""              "\\d"
    ""              "atz"
    OK              "ate1"
    OK              'at+cgdcont=1,"ip","internet.eplus.de","0.0.0.0",0,0'
    TIMEOUT         22
    OK              ATD*99#
    TIMEOUT         33
    SAY             "\\nWaiting for connect...\\n"
    CONNECT         ""
    SAY             "\\nConnected." """
                
                
PPP_DEFAULT_DISCONNECT_SCRIPT = """exec /usr/sbin/chat -V -s -S
    ABORT           "BUSY"
    ABORT           "ERROR"
    ABORT           "NO DIALTONE"
    SAY             "\nSending break to the modem\n"
    ""              "\K"
    ""              "\K"
    ""              "\K"
    ""              "+++ATH"
    ""              "+++ATH"
    ""              "+++ATH"
    "NO CARRIER"    ""
    SAY             "\nPDP context detached\n" """
                
## deafult ppp peer - will be written to /etc/ppp/peers 
## if no other peer is found                    
PPP_DEFAULT_CONFIG = """/dev/ttySAC0
novjccomp
crtscts
nodetach
defaultroute
noipdefault
disconnect /etc/ppp/peers/gprs-disconnect-chat
novj
holdoff 5
ipcp-accept-local
user eplus
password gprs
replacedefaultroute
lcp-echo-failure 40000
connect /etc/ppp/peers/gprs-connect-chat
"""
