#!/usr/bin/python
"""
 * pppdConfigParser.py - Parsing the configuration of a pppd peer
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
 *
 * Thanks to Bartek Zdanowski for changing ATDT to ATD 
 *   and suggesting #99* as dial string
 * 
 * ---
 * chat-script parsing is not complete at all 
 * we just parse what we need for gprs for now...
 * 
 * ---
 * Paramenters and how we parse them for now
 * (the once called "FREQUENTLY USED OPTIONS" in the pppd man page)
 *
 * NFC - not fully compatible (can not parse all variants yet)
 * FC - fully compatible (can parse all variants of the poarameter)
 * NFC? - manpage was not explicit enough
 *
 * ttyname              - a string starting with /dev/ (NFC)
 * speed                - a line only containing an integer (FC)
 * asyncmap <map>       - 32 Bit Hex number (withoug "0x") default 0 (mask) (FC)
 * auth                 - flag - default False (FC)
 * call <name>          - filename of a file from relative to current dir (FC)
 * connect <script>     - filename of a file from relative to current dir (NFC?)
 * crtscts              - flag - default empty (flow control unchanged) (FC)
 * nocrtscts            - flag - default empty (flow control unchanged) (FC)
 * cdtrcts              - flag - default empty (flow control unchanged) (FC)
 * nocdtrcts            - flag - default empty (flow control unchanged) (FC)
 * defaultroute         - flag - default False (prio +) (FC)
 * nodefaultroute       - flag - default True  (prio -) (FC)
 * replacedefaultroute  - flag - default False (prio ++) (FC)
 * disconnect <script>  - filename of a file from relative to current dir (NFC?)
 * escape <xx,yy,...>   - list of hex values (8 Bit) (FC)
 * file <name>          - filename of a file from relative to current dir (NFC?)
 * init <script>        - filename of a file from relative to current dir (NFC?)
 * lock                 - flag - default False (FC)
 * mru <n>              - int 128..16384 (IPv6: 1280..16384)-default 1500 (FC)
 * mtu <n>              - int 128..16384 (IPv6: 1280..16384)-default 1500?(NFC?)
 * passive              - flag - default False (FC)
 *
 * -- additional --
 * nodetach             - flag - default False (FC) K
 * holdoff              - int (FC)
 * noipdefault          - flag - default False (FC)
 * ipcp-accept-local    - flag - default False (FC)
 * novj                 - flag - default False (FC)
 * novjccomp            - flag - default False (FC)
 * defaultroute         - flag - default False (FC)
 * replacedefaultroute  - flag - default False (FC)
 * lcp-echo-interval    - int (FC)
 * lcp-echo-failure     - int (FC)
 * noauth               - flag - default False (FC)
"""


import os
import stat
from GlobalConfiguration import *
#from settingsgui.GlobalConfiguration import *


def remove_quotations(string):
    return string.lstrip("\"").lstrip("'").lstrip("\"").rstrip("'").rstrip("\"").rstrip("'")


class pppdConfigEntry:
    def __init__(self, value, default, entry_type, priority):
        self.value = value
        self.default = default
        self.entry_type = entry_type
        self.priority = priority
        

class pppdConfigParser:
    def __init__(self, filename):        
        ## format is [value, default, is_flag, priority]
        self.pppd_config = {
            ## specially parsed - single worded 
            "ttyname":  pppdConfigEntry("", "", "ttyname", 0),
            "speed": pppdConfigEntry(0, 0, "speed", 0),
        
            ## flags
            "auth": pppdConfigEntry(False, False, "flag", 0),            
            "noauth": pppdConfigEntry(False, False, "flag", 0),            
            "noipdefault": pppdConfigEntry(False, False, "flag", 0),
            "ipcp-accept-local": pppdConfigEntry(False, False, "flag", 0),
            "novj": pppdConfigEntry(False, False, "flag", 0),
            "novjccomp": pppdConfigEntry(False, False, "flag", 0),
            "defaultroute": pppdConfigEntry(False, False, "flag", 0),
            "replacedefaultroute": pppdConfigEntry(False, False, "flag", 0),            
            "nodetach": pppdConfigEntry(False, False, "flag", 0),
            "noauth": pppdConfigEntry(False, True, "flag", 0),
            "crtscts": pppdConfigEntry(-1, -1, "flag", 1),
            "nocrtscts": pppdConfigEntry(-1, -1, "flag", 0),
            "cdtrcts": pppdConfigEntry(-1, -1, "flag", 1),
            "nocdtrcts": pppdConfigEntry(-1, -1, "flag", 0),
            "defaultroute": pppdConfigEntry(False, False, "flag", 1),
            "nodefaultroute": pppdConfigEntry(True, True, "flag", 0), 
            "replacedefaultroute": pppdConfigEntry(False, False, "flag", 2),
            "lock": pppdConfigEntry(False, False, True, 0),
            "passive": pppdConfigEntry(False, False, True, 0),

            ## options with a singe filename (path) argument 
            "call": pppdConfigEntry("", "", "path", 0),
            "connect": pppdConfigEntry("", "", "path", 0),
            "disconnect": pppdConfigEntry("", "", "path", 0),
            "file": pppdConfigEntry("", "", "path", 0),
            "init": pppdConfigEntry("", "", "path", 0),
            
            ## options with a single int argument
            "mru": pppdConfigEntry(1500, 1500, "int", 0),
            "mtu": pppdConfigEntry(1500, 1500, "int", 0),
            "holdoff": pppdConfigEntry(0, 0, "int", 0),
            "lcp-echo-failure": pppdConfigEntry(0, 0, "int", 0),
            "lcp-echo-failure": pppdConfigEntry(0, 0, "int", 0),
            
            ## options with a single string argument
            "user": pppdConfigEntry("", "", "string", 0),
            "password": pppdConfigEntry("", "", "string", 0),
            
            ## options with specially parsed arguments
            "asyncmap": pppdConfigEntry(0, 0, "asyncmap", 0), 
            "escape": pppdConfigEntry([], [], "escape", 0),
        }
        self.connect_script = ""
        self.disconnect_script = ""
        self.secrets = {}
        self.parse_pppd_config(filename)
        self.parse_secrets(PPP_SECRETS_FILES)
        self.APN = ""
        self.number = ""
        self.config_name = ""
        
    def generate_configuration(self, config_path, config_name, APN, 
                                                        user, password, number):
        pppd_config = self.pppd_config
        self.APN = APN
        self.config_name = config_name
        pppd_config["user"].value = user
        pppd_config["password"].value = password
        self.number = number.rstrip('#')
        pppd_config["connect"].value = "%s-connect-chat" % (config_path+config_name)
        pppd_config["disconnect"].value = "%s-disconnect-chat" % (config_path+config_name)
        self.write_pppd_config_to_file(pppd_config, 
                            os.path.join(config_path, config_name))
        return True
        
        
        
    def get_APN(self):
        if len (self.APN) >= 1:
            return self.APN
        if len(self.connect_script) >= 1:
            for line in self.connect_script:
                if line.upper().find("AT+CGDCONT=1") >= 0:
                    APN = remove_quotations(line.split(',')[2])
                    self.APN = APN
                    return APN
        return ""
        
    def get_number(self):
        if len (self.number) >= 1:
            return self.number

        if len(self.connect_script) >= 1:
            for line in self.connect_script:
                if line.upper().find("ATD") >= 0\
                                            or line.upper().find("ATDT") >= 0:
                    for word in line.split():
                        if word.upper().find("ATDT") >= 0:
                            self.number = word.lower().replace("atdt", "") + "#"
                            return word.lower().replace("atdt", "") + "#"
                        if word.upper().find("ATD") >= 0:
                            self.number = word.lower().replace("atd", "") + "#"
                            return word.lower().replace("atd", "") + "#"
        return ""

    def get_user(self):
        return self.pppd_config["user"].value

    def get_password(self):
        if len(self.pppd_config["password"].value) >= 1:
            return self.pppd_config["password"].value
        else:
            if self.secrets.has_key(self.pppd_config["user"].value):
                return self.secrets[self.pppd_config["user"].value]
        return ""
                        
    def parse_chat_script(self, filename):    
        chat_script_lines = []
        try:
            file_handle = open(filename)        
        except:    
            print "could not open chat script %s - error in pppd config file!" % filename 
            return []
            
#        print "parsing chat script: %s" % filename
        
        for line in file_handle.readlines():
            line = line.rstrip('\n')
            line = line.split('#')[0]   # remove comments <- ToDo this ignores strings containing '#'!
            if len(line.split()) >= 1:  # remove empty lines
                chat_script_lines.append(line.rstrip("\\").rstrip().lstrip())
        file_handle.close()
        return chat_script_lines
        

    ## parsing secrets and placing the last found user/pass combination
    ## into self.secrets
    ## format is:
    ## "user" ignored "pass"
    ## while where ignoring everything other than user and path 
    ## - second argument has to be there use *
    def parse_secrets(self, secret_files):
        for filename in secret_files:
            if not os.path.exists(filename):
                break
            try:
                file_handle = open(filename)
            except:
                break
#            print "opened %s" % filename
            for line in file_handle.readlines():
                line = line.split('#')[0]  # remove comments
                if len(line.split()) >= 3: # removing unvalid lines
                    user = remove_quotations(line.split()[0])
                    password = remove_quotations(line.split()[2])
                    self.secrets[user] = password
#                    print "added %s:%s" % (user, password)
                            

    def parse_pppd_config(self, filename):   
        file_handle = open(filename)
        for line in file_handle.readlines():
            line = line.rstrip('\n')
            line = line.split('#')[0]   # remove comments
            if len(line.split()) >= 1:  # remove empty lines
                self.set_value_from_line(line)
        file_handle.close()
        if len(self.pppd_config["connect"].value) > 0:
            self.connect_script = self.parse_chat_script(self.pppd_config["connect"].value)
        if len(self.pppd_config["disconnect"].value) > 0:
            self.disconnect_script = self.parse_chat_script(self.pppd_config["disconnect"].value)
        ## ToDo: call, file, init
                            
                
    def set_value_from_line(self, line):
        ## no keyword in line - so not found in dictionary
        if line.split()[0].isdigit():
            self.pppd_config["speed"].value = int(line.split()[0])
        elif (len(line.split()) == 1) and (line.split()[0].startswith("/dev/")):
            self.pppd_config["ttyname"].value = line.split()[0]
        
        for key in self.pppd_config.keys():
            if key == line.split()[0]:    # split to only find whole words
                ## flags
                if self.pppd_config[key].entry_type == "flag":
                    self.pppd_config[key].value = True
                ## options with argument(s)
                if len(line.split()) >= 2:
                    if self.pppd_config[key].entry_type == "path":
                        self.pppd_config[key].value = remove_quotations(line.split()[1])
                    elif self.pppd_config[key].entry_type == "int":
                        if remove_quotations(line.split()[1]).isdigit():
                            self.pppd_config[key].value = int(remove_quotations(line.split()[1]))
                    elif self.pppd_config[key].entry_type == "string":
                        self.pppd_config[key].value = remove_quotations(line.split()[1])
                    elif self.pppd_config[key].entry_type == "asyncmap":
                        # no hex conversion needed - saved as string
                        self.pppd_config[key].value = remove_quotations(line.split()[1])
                    elif self.pppd_config[key].entry_type == "escape":
                        self.pppd_config[key].value = remove_quotations(line.split()[1].lstrip("\""))
        
        
    def write_chat_script(self, script, filename):
        if script == "connect":
            filename = filename
            file_handle = open(filename, 'w')
            file_handle.write("#!/bin/sh\n")
            for line in PPP_DEFAULT_CONNECT_SCRIPT.split('\n'):
                if line.upper().find("AT+CGDCONT=1") >= 0:
                    line = "    OK              'at+cgdcont=1,\"ip\",\"%s\",\"0.0.0.0\",0,0'" % self.get_APN()
                if line.upper().find("ATD")>=0 or line.upper().find("ATDT")>=0:
                    ## the '#' is essential - and was removed as commend sign
                    line = "    OK              atd%s#" % self.get_number()     
                file_handle.write("%s\\\n" % line)
            file_handle.close()
            ## make executable
            tmp_stat = stat.S_IMODE(os.stat(filename).st_mode)
            os.chmod(filename, tmp_stat | stat.S_IXUSR)
            print "wrote chat script to %s" % filename
        
        if script == "disconnect":
            filename = filename
            file_handle = open(filename, 'w')
            file_handle.write("#!/bin/sh\n")
            for line in PPP_DEFAULT_CONNECT_SCRIPT.split('\n'):
                file_handle.write("%s\\\n" % line)
            file_handle.close()
            ## make executable
            tmp_stat = stat.S_IMODE(os.stat(filename).st_mode)
            os.chmod(filename, tmp_stat | stat.S_IXUSR)
            print "wrote chat script to %s" % filename

        
    def write_pppd_config_to_file(self, pppd_config, filename):
        file_handle = open(filename, 'w')

        file_handle.write("# pppd configuration file - generated by SettingGUI\n")
        file_handle.write("# bug reports to kristian-m@kristian-m.de\n\n")

        if pppd_config["ttyname"].value != "":
            file_handle.write("%s\n" % pppd_config["ttyname"].value)
        
        if pppd_config["speed"].value != 0:
            file_handle.write("%s\n" % pppd_config["speed"].value)
        
        for key in pppd_config.keys():
            if pppd_config[key].value != pppd_config[key].default:
                ## flags
                if pppd_config[key].entry_type == "flag":
                        ## key must be the flag name!
                        if pppd_config[key].value:
                            file_handle.write("%s\n" % key)
                ## one string argument
                if ((pppd_config[key].entry_type == "int") or
                        (pppd_config[key].entry_type == "string") or
                        (pppd_config[key].entry_type == "asyncmap")):
                    ## key must be the option name!
                    file_handle.write("%s %s\n" % (key, pppd_config[key].value))
                    if key == "user":
                        file_handle.write("%s %s\n" % ("password", self.get_password()))
                    
                ## the escape list 
                if pppd_config[key].entry_type == "escape":
                    file_handle.write("%s %s\n" % (key, 
                                            ",".join(pppd_config[key].value)))
                if (pppd_config[key].entry_type == "path"):                    
                    file_handle.write("%s %s\n" % (key, pppd_config[key].value))
                    if key == "connect":
                        self.write_chat_script("connect", pppd_config[key].value)
                    if key == "disconnect":
                        self.write_chat_script("disconnect", pppd_config[key].value)
                    
            ## end of for loop
        file_handle.close()
        print "wrote pppd config file to %s" % filename


    """
    ToDo, other options:

<local_IP_address>:<remote_IP_address>
    Set the local and/or remote interface IP addresses. Either one may be omitted. The IP addresses can be specified with a host name or in decimal dot notation (e.g. 150.234.56.78). The default local address is the (first) IP address of the system (unless the noipdefault option is given). The remote address will be obtained from the peer if not specified in any option. Thus, in simple cases, this option is not required. If a local and/or remote IP address is specified with this option, pppd will not accept a different value from the peer in the IPCP negotiation, unless the ipcp-accept-local and/or ipcp-accept-remote options are given, respectively. 
ipv6 <local_interface_identifier>,<remote_interface_identifier>
    Set the local and/or remote 64-bit interface identifier. Either one may be omitted. The identifier must be specified in standard ascii notation of IPv6 addresses (e.g. ::dead:beef). If the ipv6cp-use-ipaddr option is given, the local identifier is the local IPv4 address (see above). On systems which supports a unique persistent id, such as EUI-48 derived from the Ethernet MAC address, ipv6cp-use-persistent option can be used to replace the ipv6 <local>,<remote> option. Otherwise the identifier is randomized. 
active-filter filter-expression
    Specifies a packet filter to be applied to data packets to determine which packets are to be regarded as link activity, and therefore reset the idle timer, or cause the link to be brought up in demand-dialling mode. This option is useful in conjunction with the idle option if there are packets being sent or received regularly over the link (for example, routing information packets) which would otherwise prevent the link from ever appearing to be idle. The filter-expression syntax is as described for tcpdump(1), except that qualifiers which are inappropriate for a PPP link, such as ether and arp, are not permitted. Generally the filter expression should be enclosed in single-quotes to prevent whitespace in the expression from being interpreted by the shell. This option is currently only available under Linux, and requires that the kernel was configured to include PPP filtering support (CONFIG_PPP_FILTER). Note that it is possible to apply different constraints to incoming and outgoing packets using the inbound and outbound qualifiers. 
allow-ip address(es)
    Allow peers to use the given IP address or subnet without authenticating themselves. The parameter is parsed as for each element of the list of allowed IP addresses in the secrets files (see the AUTHENTICATION section below). 
allow-number number
    Allow peers to connect from the given telephone number. A trailing '*' character will match all numbers beginning with the leading part. 
bsdcomp nr,nt
    Request that the peer compress packets that it sends, using the BSD-Compress scheme, with a maximum code size of nr bits, and agree to compress packets sent to the peer with a maximum code size of nt bits. If nt is not specified, it defaults to the value given for nr. Values in the range 9 to 15 may be used for nr and nt; larger values give better compression but consume more kernel memory for compression dictionaries. Alternatively, a value of 0 for nr or nt disables compression in the corresponding direction. Use nobsdcomp or bsdcomp 0 to disable BSD-Compress compression entirely. 
cdtrcts
    Use a non-standard hardware flow control (i.e. DTR/CTS) to control the flow of data on the serial port. If neither the crtscts, the nocrtscts, the cdtrcts nor the nocdtrcts option is given, the hardware flow control setting for the serial port is left unchanged. Some serial ports (such as Macintosh serial ports) lack a true RTS output. Such serial ports use this mode to implement true bi-directional flow control. The sacrifice is that this flow control mode does not permit using DTR as a modem control line. 
chap-interval n
    If this option is given, pppd will rechallenge the peer every n seconds. 
chap-max-challenge n
    Set the maximum number of CHAP challenge transmissions to n (default 10). 
chap-restart n
    Set the CHAP restart interval (retransmission timeout for challenges) to n seconds (default 3). 
child-timeout n
    When exiting, wait for up to n seconds for any child processes (such as the command specified with the pty command) to exit before exiting. At the end of the timeout, pppd will send a SIGTERM signal to any remaining child processes and exit. A value of 0 means no timeout, that is, pppd will wait until all child processes have exited. 
connect-delay n
    Wait for up to n milliseconds after the connect script finishes for a valid PPP packet from the peer. At the end of this time, or when a valid PPP packet is received from the peer, pppd will commence negotiation by sending its first LCP packet. The default value is 1000 (1 second). This wait period only applies if the connect or pty option is used. 
debug
    Enables connection debugging facilities. If this option is given, pppd will log the contents of all control packets sent or received in a readable form. The packets are logged through syslog with facility daemon and level debug. This information can be directed to a file by setting up /etc/syslog.conf appropriately (see syslog.conf(5)). 
default-asyncmap
    Disable asyncmap negotiation, forcing all control characters to be escaped for both the transmit and the receive direction. 
default-mru
    Disable MRU [Maximum Receive Unit] negotiation. With this option, pppd will use the default MRU value of 1500 bytes for both the transmit and receive direction. 
deflate nr,nt
    Request that the peer compress packets that it sends, using the Deflate scheme, with a maximum window size of 2**nr bytes, and agree to compress packets sent to the peer with a maximum window size of 2**nt bytes. If nt is not specified, it defaults to the value given for nr. Values in the range 9 to 15 may be used for nr and nt; larger values give better compression but consume more kernel memory for compression dictionaries. Alternatively, a value of 0 for nr or nt disables compression in the corresponding direction. Use nodeflate or deflate 0 to disable Deflate compression entirely. (Note: pppd requests Deflate compression in preference to BSD-Compress if the peer can do either.) 
demand
    Initiate the link only on demand, i.e. when data traffic is present. With this option, the remote IP address must be specified by the user on the command line or in an options file. Pppd will initially configure the interface and enable it for IP traffic without connecting to the peer. When traffic is available, pppd will connect to the peer and perform negotiation, authentication, etc. When this is completed, pppd will commence passing data packets (i.e., IP packets) across the link.

    The demand option implies the persist option. If this behaviour is not desired, use the nopersist option after the demand option. The idle and holdoff options are also useful in conjuction with the demand option. 
domain d
    Append the domain name d to the local host name for authentication purposes. For example, if gethostname() returns the name porsche, but the fully qualified domain name is porsche.Quotron.COM, you could specify domain Quotron.COM. Pppd would then use the name porsche.Quotron.COM for looking up secrets in the secrets file, and as the default name to send to the peer when authenticating itself to the peer. This option is privileged. 
dryrun
    With the dryrun option, pppd will print out all the option values which have been set and then exit, after parsing the command line and options files and checking the option values, but before initiating the link. The option values are logged at level info, and also printed to standard output unless the device on standard output is the device that pppd would be using to communicate with the peer. 
dump
    With the dump option, pppd will print out all the option values which have been set. This option is like the dryrun option except that pppd proceeds as normal rather than exiting. 
endpoint <epdisc>
    Sets the endpoint discriminator sent by the local machine to the peer during multilink negotiation to <epdisc>. The default is to use the MAC address of the first ethernet interface on the system, if any, otherwise the IPv4 address corresponding to the hostname, if any, provided it is not in the multicast or locally-assigned IP address ranges, or the localhost address. The endpoint discriminator can be the string null or of the form type:value, where type is a decimal number or one of the strings local, IP, MAC, magic, or phone. The value is an IP address in dotted-decimal notation for the IP type, or a string of bytes in hexadecimal, separated by periods or colons for the other types. For the MAC type, the value may also be the name of an ethernet or similar network interface. This option is currently only available under Linux. 
eap-interval n
    If this option is given and pppd authenticates the peer with EAP (i.e., is the server), pppd will restart EAP authentication every n seconds. For EAP SRP-SHA1, see also the srp-interval option, which enables lightweight rechallenge. 
eap-max-rreq n
    Set the maximum number of EAP Requests to which pppd will respond (as a client) without hearing EAP Success or Failure. (Default is 20.) 
eap-max-sreq n
    Set the maximum number of EAP Requests that pppd will issue (as a server) while attempting authentication. (Default is 10.) 
eap-restart n
    Set the retransmit timeout for EAP Requests when acting as a server (authenticator). (Default is 3 seconds.) 
eap-timeout n
    Set the maximum time to wait for the peer to send an EAP Request when acting as a client (authenticatee). (Default is 20 seconds.) 
hide-password
    When logging the contents of PAP packets, this option causes pppd to exclude the password string from the log. This is the default. 
holdoff n
    Specifies how many seconds to wait before re-initiating the link after it terminates. This option only has any effect if the persist or demand option is used. The holdoff period is not applied if the link was terminated because it was idle. 
idle n
    Specifies that pppd should disconnect if the link is idle for n seconds. The link is idle when no data packets (i.e. IP packets) are being sent or received. Note: it is not advisable to use this option with the persist option without the demand option. If the active-filter option is given, data packets which are rejected by the specified activity filter also count as the link being idle. 
ipcp-accept-local
    With this option, pppd will accept the peer's idea of our local IP address, even if the local IP address was specified in an option. 
ipcp-accept-remote
    With this option, pppd will accept the peer's idea of its (remote) IP address, even if the remote IP address was specified in an option. 
ipcp-max-configure n
    Set the maximum number of IPCP configure-request transmissions to n (default 10). 
ipcp-max-failure n
    Set the maximum number of IPCP configure-NAKs returned before starting to send configure-Rejects instead to n (default 10). 
ipcp-max-terminate n
    Set the maximum number of IPCP terminate-request transmissions to n (default 3). 
ipcp-restart n
    Set the IPCP restart interval (retransmission timeout) to n seconds (default 3). 
ipparam string
    Provides an extra parameter to the ip-up, ip-pre-up and ip-down scripts. If this option is given, the string supplied is given as the 6th parameter to those scripts. 
ipv6cp-max-configure n
    Set the maximum number of IPv6CP configure-request transmissions to n (default 10). 
ipv6cp-max-failure n
    Set the maximum number of IPv6CP configure-NAKs returned before starting to send configure-Rejects instead to n (default 10). 
ipv6cp-max-terminate n
    Set the maximum number of IPv6CP terminate-request transmissions to n (default 3). 
ipv6cp-restart n
    Set the IPv6CP restart interval (retransmission timeout) to n seconds (default 3). 
ipx
    Enable the IPXCP and IPX protocols. This option is presently only supported under Linux, and only if your kernel has been configured to include IPX support. 
ipx-network n
    Set the IPX network number in the IPXCP configure request frame to n, a hexadecimal number (without a leading 0x). There is no valid default. If this option is not specified, the network number is obtained from the peer. If the peer does not have the network number, the IPX protocol will not be started. 
ipx-node n:m
    Set the IPX node numbers. The two node numbers are separated from each other with a colon character. The first number n is the local node number. The second number m is the peer's node number. Each node number is a hexadecimal number, at most 10 digits long. The node numbers on the ipx-network must be unique. There is no valid default. If this option is not specified then the node numbers are obtained from the peer. 
ipx-router-name <string>
    Set the name of the router. This is a string and is sent to the peer as information data. 
ipx-routing n
    Set the routing protocol to be received by this option. More than one instance of ipx-routing may be specified. The 'none' option (0) may be specified as the only instance of ipx-routing. The values may be 0 for NONE, 2 for RIP/SAP, and 4 for NLSP. 
ipxcp-accept-local
    Accept the peer's NAK for the node number specified in the ipx-node option. If a node number was specified, and non-zero, the default is to insist that the value be used. If you include this option then you will permit the peer to override the entry of the node number. 
ipxcp-accept-network
    Accept the peer's NAK for the network number specified in the ipx-network option. If a network number was specified, and non-zero, the default is to insist that the value be used. If you include this option then you will permit the peer to override the entry of the node number. 
ipxcp-accept-remote
    Use the peer's network number specified in the configure request frame. If a node number was specified for the peer and this option was not specified, the peer will be forced to use the value which you have specified. 
ipxcp-max-configure n
    Set the maximum number of IPXCP configure request frames which the system will send to n. The default is 10. 
ipxcp-max-failure n
    Set the maximum number of IPXCP NAK frames which the local system will send before it rejects the options. The default value is 3. 
ipxcp-max-terminate n
    Set the maximum nuber of IPXCP terminate request frames before the local system considers that the peer is not listening to them. The default value is 3. 
kdebug n
    Enable debugging code in the kernel-level PPP driver. The argument values depend on the specific kernel driver, but in general a value of 1 will enable general kernel debug messages. (Note that these messages are usually only useful for debugging the kernel driver itself.) For the Linux 2.2.x kernel driver, the value is a sum of bits: 1 to enable general debug messages, 2 to request that the contents of received packets be printed, and 4 to request that the contents of transmitted packets be printed. On most systems, messages printed by the kernel are logged by syslog(1) to a file as directed in the /etc/syslog.conf configuration file. 
ktune
    Enables pppd to alter kernel settings as appropriate. Under Linux, pppd will enable IP forwarding (i.e. set /proc/sys/net/ipv4/ip_forward to 1) if the proxyarp option is used, and will enable the dynamic IP address option (i.e. set /proc/sys/net/ipv4/ip_dynaddr to 1) in demand mode if the local address changes. 
lcp-echo-failure n
    If this option is given, pppd will presume the peer to be dead if n LCP echo-requests are sent without receiving a valid LCP echo-reply. If this happens, pppd will terminate the connection. Use of this option requires a non-zero value for the lcp-echo-interval parameter. This option can be used to enable pppd to terminate after the physical connection has been broken (e.g., the modem has hung up) in situations where no hardware modem control lines are available. 
lcp-echo-interval n
    If this option is given, pppd will send an LCP echo-request frame to the peer every n seconds. Normally the peer should respond to the echo-request by sending an echo-reply. This option can be used with the lcp-echo-failure option to detect that the peer is no longer connected. 
lcp-max-configure n
    Set the maximum number of LCP configure-request transmissions to n (default 10). 
lcp-max-failure n
    Set the maximum number of LCP configure-NAKs returned before starting to send configure-Rejects instead to n (default 10). 
lcp-max-terminate n
    Set the maximum number of LCP terminate-request transmissions to n (default 3). 
lcp-restart n
    Set the LCP restart interval (retransmission timeout) to n seconds (default 3). 
linkname name
    Sets the logical name of the link to name. Pppd will create a file named ppp-name.pid in /var/run (or /etc/ppp on some systems) containing its process ID. This can be useful in determining which instance of pppd is responsible for the link to a given peer system. This is a privileged option. 
local
    Don't use the modem control lines. With this option, pppd will ignore the state of the CD (Carrier Detect) signal from the modem and will not change the state of the DTR (Data Terminal Ready) signal. This is the opposite of the modem option. 
logfd n
    Send log messages to file descriptor n. Pppd will send log messages to at most one file or file descriptor (as well as sending the log messages to syslog), so this option and the logfile option are mutually exclusive. The default is for pppd to send log messages to stdout (file descriptor 1), unless the serial port is already open on stdout. 
logfile filename
    Append log messages to the file filename (as well as sending the log messages to syslog). The file is opened with the privileges of the user who invoked pppd, in append mode. 
login
    Use the system password database for authenticating the peer using PAP, and record the user in the system wtmp file. Note that the peer must have an entry in the /etc/ppp/pap-secrets file as well as the system password database to be allowed access. 
maxconnect n
    Terminate the connection when it has been available for network traffic for n seconds (i.e. n seconds after the first network control protocol comes up). 
maxfail n
    Terminate after n consecutive failed connection attempts. A value of 0 means no limit. The default value is 10. 
modem
    Use the modem control lines. This option is the default. With this option, pppd will wait for the CD (Carrier Detect) signal from the modem to be asserted when opening the serial device (unless a connect script is specified), and it will drop the DTR (Data Terminal Ready) signal briefly when the connection is terminated and before executing the connect script. On Ultrix, this option implies hardware flow control, as for the crtscts option. This is the opposite of the local option. 
mp
    Enables the use of PPP multilink; this is an alias for the 'multilink' option. This option is currently only available under Linux. 
mppe-stateful
    Allow MPPE to use stateful mode. Stateless mode is still attempted first. The default is to disallow stateful mode. 
mpshortseq
    Enables the use of short (12-bit) sequence numbers in multilink headers, as opposed to 24-bit sequence numbers. This option is only available under Linux, and only has any effect if multilink is enabled (see the multilink option). 
mrru n
    Sets the Maximum Reconstructed Receive Unit to n. The MRRU is the maximum size for a received packet on a multilink bundle, and is analogous to the MRU for the individual links. This option is currently only available under Linux, and only has any effect if multilink is enabled (see the multilink option). 
ms-dns <addr>
    If pppd is acting as a server for Microsoft Windows clients, this option allows pppd to supply one or two DNS (Domain Name Server) addresses to the clients. The first instance of this option specifies the primary DNS address; the second instance (if given) specifies the secondary DNS address. (This option was present in some older versions of pppd under the name dns-addr.) 
ms-wins <addr>
    If pppd is acting as a server for Microsoft Windows or "Samba" clients, this option allows pppd to supply one or two WINS (Windows Internet Name Services) server addresses to the clients. The first instance of this option specifies the primary WINS address; the second instance (if given) specifies the secondary WINS address. 
multilink
    Enables the use of the PPP multilink protocol. If the peer also supports multilink, then this link can become part of a bundle between the local system and the peer. If there is an existing bundle to the peer, pppd will join this link to that bundle, otherwise pppd will create a new bundle. See the MULTILINK section below. This option is currently only available under Linux. 
name name
    Set the name of the local system for authentication purposes to name. This is a privileged option. With this option, pppd will use lines in the secrets files which have name as the second field when looking for a secret to use in authenticating the peer. In addition, unless overridden with the user option, name will be used as the name to send to the peer when authenticating the local system to the peer. (Note that pppd does not append the domain name to name.) 
noaccomp
    Disable Address/Control compression in both directions (send and receive). 
noauth
    Do not require the peer to authenticate itself. This option is privileged. 
nobsdcomp
    Disables BSD-Compress compression; pppd will not request or agree to compress packets using the BSD-Compress scheme. 
noccp
    Disable CCP (Compression Control Protocol) negotiation. This option should only be required if the peer is buggy and gets confused by requests from pppd for CCP negotiation. 
nocrtscts
    Disable hardware flow control (i.e. RTS/CTS) on the serial port. If neither the crtscts nor the nocrtscts nor the cdtrcts nor the nocdtrcts option is given, the hardware flow control setting for the serial port is left unchanged. 
nocdtrcts
    This option is a synonym for nocrtscts. Either of these options will disable both forms of hardware flow control. 
nodefaultroute
    Disable the defaultroute option. The system administrator who wishes to prevent users from creating default routes with pppd can do so by placing this option in the /etc/ppp/options file. 
nodeflate
    Disables Deflate compression; pppd will not request or agree to compress packets using the Deflate scheme. 
nodetach
    Don't detach from the controlling terminal. Without this option, if a serial device other than the terminal on the standard input is specified, pppd will fork to become a background process. 
noendpoint
    Disables pppd from sending an endpoint discriminator to the peer or accepting one from the peer (see the MULTILINK section below). This option should only be required if the peer is buggy. 
noip
    Disable IPCP negotiation and IP communication. This option should only be required if the peer is buggy and gets confused by requests from pppd for IPCP negotiation. 
noipv6
    Disable IPv6CP negotiation and IPv6 communication. This option should only be required if the peer is buggy and gets confused by requests from pppd for IPv6CP negotiation. 
noipdefault
    Disables the default behaviour when no local IP address is specified, which is to determine (if possible) the local IP address from the hostname. With this option, the peer will have to supply the local IP address during IPCP negotiation (unless it specified explicitly on the command line or in an options file). 
noipx
    Disable the IPXCP and IPX protocols. This option should only be required if the peer is buggy and gets confused by requests from pppd for IPXCP negotiation. 
noktune
    Opposite of the ktune option; disables pppd from changing system settings. 
nolock
    Opposite of the lock option; specifies that pppd should not create a UUCP-style lock file for the serial device. This option is privileged. 
nolog
    Do not send log messages to a file or file descriptor. This option cancels the logfd and logfile options. 
nomagic
    Disable magic number negotiation. With this option, pppd cannot detect a looped-back line. This option should only be needed if the peer is buggy. 
nomp
    Disables the use of PPP multilink. This option is currently only available under Linux. 
nomppe
    Disables MPPE (Microsoft Point to Point Encryption). This is the default. 
nomppe-40
    Disable 40-bit encryption with MPPE. 
nomppe-128
    Disable 128-bit encryption with MPPE. 
nomppe-stateful
    Disable MPPE stateful mode. This is the default. 
nompshortseq
    Disables the use of short (12-bit) sequence numbers in the PPP multilink protocol, forcing the use of 24-bit sequence numbers. This option is currently only available under Linux, and only has any effect if multilink is enabled. 
nomultilink
    Disables the use of PPP multilink. This option is currently only available under Linux. 
nopcomp
    Disable protocol field compression negotiation in both the receive and the transmit direction. 
nopersist
    Exit once a connection has been made and terminated. This is the default unless the persist or demand option has been specified. 
nopredictor1
    Do not accept or agree to Predictor-1 compression. 
noproxyarp
    Disable the proxyarp option. The system administrator who wishes to prevent users from creating proxy ARP entries with pppd can do so by placing this option in the /etc/ppp/options file. 
notty
    Normally, pppd requires a terminal device. With this option, pppd will allocate itself a pseudo-tty master/slave pair and use the slave as its terminal device. Pppd will create a child process to act as a 'character shunt' to transfer characters between the pseudo-tty master and its standard input and output. Thus pppd will transmit characters on its standard output and receive characters on its standard input even if they are not terminal devices. This option increases the latency and CPU overhead of transferring data over the ppp interface as all of the characters sent and received must flow through the character shunt process. An explicit device name may not be given if this option is used. 
novj
    Disable Van Jacobson style TCP/IP header compression in both the transmit and the receive direction. 
novjccomp
    Disable the connection-ID compression option in Van Jacobson style TCP/IP header compression. With this option, pppd will not omit the connection-ID byte from Van Jacobson compressed TCP/IP headers, nor ask the peer to do so. 
papcrypt
    Indicates that all secrets in the /etc/ppp/pap-secrets file which are used for checking the identity of the peer are encrypted, and thus pppd should not accept a password which, before encryption, is identical to the secret from the /etc/ppp/pap-secrets file. 
pap-max-authreq n
    Set the maximum number of PAP authenticate-request transmissions to n (default 10). 
pap-restart n
    Set the PAP restart interval (retransmission timeout) to n seconds (default 3). 
pap-timeout n
    Set the maximum time that pppd will wait for the peer to authenticate itself with PAP to n seconds (0 means no limit). 
pass-filter filter-expression
    Specifies a packet filter to applied to data packets being sent or received to determine which packets should be allowed to pass. Packets which are rejected by the filter are silently discarded. This option can be used to prevent specific network daemons (such as routed) using up link bandwidth, or to provide a very basic firewall capability. The filter-expression syntax is as described for tcpdump(1), except that qualifiers which are inappropriate for a PPP link, such as ether and arp, are not permitted. Generally the filter expression should be enclosed in single-quotes to prevent whitespace in the expression from being interpreted by the shell. Note that it is possible to apply different constraints to incoming and outgoing packets using the inbound and outbound qualifiers. This option is currently only available under Linux, and requires that the kernel was configured to include PPP filtering support (CONFIG_PPP_FILTER). 
password password-string
    Specifies the password to use for authenticating to the peer. Use of this option is discouraged, as the password is likely to be visible to other users on the system (for example, by using ps(1)). 
persist
    Do not exit after a connection is terminated; instead try to reopen the connection. The maxfail option still has an effect on persistent connections. 
plugin filename
    Load the shared library object file filename as a plugin. This is a privileged option. If filename does not contain a slash (/), pppd will look in the /usr/lib/pppd/version directory for the plugin, where version is the version number of pppd (for example, 2.4.2). 
predictor1
    Request that the peer compress frames that it sends using Predictor-1 compression, and agree to compress transmitted frames with Predictor-1 if requested. This option has no effect unless the kernel driver supports Predictor-1 compression. 
privgroup group-name
    Allows members of group group-name to use privileged options. This is a privileged option. Use of this option requires care as there is no guarantee that members of group-name cannot use pppd to become root themselves. Consider it equivalent to putting the members of group-name in the kmem or disk group. 
proxyarp
    Add an entry to this system's ARP [Address Resolution Protocol] table with the IP address of the peer and the Ethernet address of this system. This will have the effect of making the peer appear to other systems to be on the local ethernet. 
pty script
    Specifies that the command script is to be used to communicate rather than a specific terminal device. Pppd will allocate itself a pseudo-tty master/slave pair and use the slave as its terminal device. The script will be run in a child process with the pseudo-tty master as its standard input and output. An explicit device name may not be given if this option is used. (Note: if the record option is used in conjuction with the pty option, the child process will have pipes on its standard input and output.) 
receive-all
    With this option, pppd will accept all control characters from the peer, including those marked in the receive asyncmap. Without this option, pppd will discard those characters as specified in RFC1662. This option should only be needed if the peer is buggy. 
record filename
    Specifies that pppd should record all characters sent and received to a file named filename. This file is opened in append mode, using the user's user-ID and permissions. This option is implemented using a pseudo-tty and a process to transfer characters between the pseudo-tty and the real serial device, so it will increase the latency and CPU overhead of transferring data over the ppp interface. The characters are stored in a tagged format with timestamps, which can be displayed in readable form using the pppdump(8) program. 
remotename name
    Set the assumed name of the remote system for authentication purposes to name. 
remotenumber number
    Set the assumed telephone number of the remote system for authentication purposes to number. 
refuse-chap
    With this option, pppd will not agree to authenticate itself to the peer using CHAP. 
refuse-mschap
    With this option, pppd will not agree to authenticate itself to the peer using MS-CHAP. 
refuse-mschap-v2
    With this option, pppd will not agree to authenticate itself to the peer using MS-CHAPv2. 
refuse-eap
    With this option, pppd will not agree to authenticate itself to the peer using EAP. 
refuse-pap
    With this option, pppd will not agree to authenticate itself to the peer using PAP. 
require-chap
    Require the peer to authenticate itself using CHAP [Challenge Handshake Authentication Protocol] authentication. 
require-mppe
    Require the use of MPPE (Microsoft Point to Point Encryption). This option disables all other compression types. This option enables both 40-bit and 128-bit encryption. In order for MPPE to successfully come up, you must have authenticated with either MS-CHAP or MS-CHAPv2. This option is presently only supported under Linux, and only if your kernel has been configured to include MPPE support. 
require-mppe-40
    Require the use of MPPE, with 40-bit encryption. 
require-mppe-128
    Require the use of MPPE, with 128-bit encryption. 
require-mschap
    Require the peer to authenticate itself using MS-CHAP [Microsoft Challenge Handshake Authentication Protocol] authentication. 
require-mschap-v2
    Require the peer to authenticate itself using MS-CHAPv2 [Microsoft Challenge Handshake Authentication Protocol, Version 2] authentication. 
require-eap
    Require the peer to authenticate itself using EAP [Extensible Authentication Protocol] authentication. 
require-pap
    Require the peer to authenticate itself using PAP [Password Authentication Protocol] authentication. 
show-password
    When logging the contents of PAP packets, this option causes pppd to show the password string in the log message. 
silent
    With this option, pppd will not transmit LCP packets to initiate a connection until a valid LCP packet is received from the peer (as for the 'passive' option with ancient versions of pppd). 
srp-interval n
    If this parameter is given and pppd uses EAP SRP-SHA1 to authenticate the peer (i.e., is the server), then pppd will use the optional lightweight SRP rechallenge mechanism at intervals of n seconds. This option is faster than eap-interval reauthentication because it uses a hash-based mechanism and does not derive a new session key. 
srp-pn-secret string
    Set the long-term pseudonym-generating secret for the server. This value is optional and if set, needs to be known at the server (authenticator) side only, and should be different for each server (or poll of identical servers). It is used along with the current date to generate a key to encrypt and decrypt the client's identity contained in the pseudonym. 
srp-use-pseudonym
    When operating as an EAP SRP-SHA1 client, attempt to use the pseudonym stored in ~/.ppp_psuedonym first as the identity, and save in this file any pseudonym offered by the peer during authentication. 
sync
    Use synchronous HDLC serial encoding instead of asynchronous. The device used by pppd with this option must have sync support. Currently supports Microgate SyncLink adapters under Linux and FreeBSD 2.2.8 and later. 
unit num
    Sets the ppp unit number (for a ppp0 or ppp1 etc interface name) for outbound connections. 
updetach
    With this option, pppd will detach from its controlling terminal once it has successfully established the ppp connection (to the point where the first network control protocol, usually the IP control protocol, has come up). 
usehostname
    Enforce the use of the hostname (with domain name appended, if given) as the name of the local system for authentication purposes (overrides the name option). This option is not normally needed since the name option is privileged. 
usepeerdns
    Ask the peer for up to 2 DNS server addresses. The addresses supplied by the peer (if any) are passed to the /etc/ppp/ip-up script in the environment variables DNS1 and DNS2, and the environment variable USEPEERDNS will be set to 1. In addition, pppd will create an /var/run/ppp/resolv.conf file containing one or two nameserver lines with the address(es) supplied by the peer. 
user name
    Sets the name used for authenticating the local system to the peer to name. 
vj-max-slots n
    Sets the number of connection slots to be used by the Van Jacobson TCP/IP header compression and decompression code to n, which must be between 2 and 16 (inclusive). 
welcome script
    Run the executable or shell command specified by script before initiating PPP negotiation, after the connect script (if any) has completed. A value for this option from a privileged source cannot be overridden by a non-privileged user. 
xonxoff
    Use software flow control (i.e. XON/XOFF) to control the flow of data on the serial port.

    """







