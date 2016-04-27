# BLE iBeaconScanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# JCS 06/07/14
# Adapted for Python3 by Michael duPont 2015-04-05

# BLE scanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# BLE scanner, based on https://code.google.com/p/pybluez/source/browse/trunk/examples/advanced/inquiry-with-rssi.py

# https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c for lescan
# https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.6/lib/hci.h for opcodes
# https://github.com/pauloborges/bluez/blob/master/lib/hci.c#L2782 for functions used by lescan

# performs a simple device inquiry, and returns a list of ble advertizements discovered
# device

#Installation
#sudo apt-get install libbluetooth-dev bluez
#sudo pip-3.2 install pybluez   #pip-3.2 for Python3.2 on Raspberry Pi

import sys
import struct
import bluetooth._bluetooth as bluez
import mysql.connector
import time
from datetime import date, datetime, timedelta
import httplib2
import json
import urllib
from urllib.error import URLError

OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_ENABLE=0x000C

def hci_enable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x01)

def hci_disable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x00)

def hci_toggle_le_scan(sock, enable):
    cmd_pkt = struct.pack("<BB", enable, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)

def hci_le_set_scan_parameters(sock):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)

def extract (pkt):
    """Split the ibeacon packet into understandable parts"""
    uuidfmt = "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x"

    raw = (("%02x " * 40) % struct.unpack ('B' * 40, pkt[:])).strip ()

    mac = ("%02x:%02x:%02x:%02x:%02x:%02x") % struct.unpack ('B' * 6, pkt[3:9])
    uuid = uuidfmt % struct.unpack ('B' * 16, pkt[18:18+16])
    major = ("%02x " * 2) % struct.unpack ('B' * 2, pkt[34:36])
    minor = ("%02x " * 2) % struct.unpack ('B' * 2, pkt[36:38])
    tx = "%d" % (struct.unpack ('B', pkt[38:39])[0] - 256)
    strength =struct.unpack ('B', pkt[39:40])[0] - 256

    return raw, mac, uuid, major, minor, tx, strength

def split_packets (pkts):
    """Strip a combined packet into a list of packets"""
    n = 40
    i = 1
    length, = struct.unpack ("B", pkts[:1])
    pktslist = []
    while i < length:
        pktslist.append (pkts[1+i*length:1+i*length+n])
        i += n
    return pktslist

def parse_events(sock, loop_count=100):
    old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    flt = bluez.hci_filter_new()

    bluez.hci_filter_all_events (flt)
    bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)

    sock.setsockopt (bluez.SOL_HCI, bluez.HCI_FILTER, flt)

    results = []

    for i in range(0, loop_count):
        pkt = sock.recv(255)

        event, subevent, something = struct.unpack ("BBB", pkt[1:4])
        if subevent != 42: continue

        for p in split_packets (pkt): results.append (extract (p))

    sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, old_filter)
    return results
interval = 10

def main ():
    seen={}
    lastposted = datetime.now()
    while True:
        beacons = parse_events(sock, interval)
        for raw, mac, uuid, major, minor, tx, strength in beacons:
            print ('> ', raw);
            print ('  ', uuid, 'M', major, 'm', minor)
            print ('  ', 'tx', tx, 's', strength)

            now = datetime.now()
            if uuid in seen and (now - seen[uuid]).seconds<1: continue
            seen[uuid]=now

            if (now - lastposted).seconds >  interval:
                password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                
                top_level_url = "http://11301770.pxl-ea-ict.be/web"
                password_mgr.add_password(None, top_level_url, 'admin', 'admin')

                handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

                opener = urllib.request.build_opener(handler)

                #opener.open(a_url)
                urllib.request.install_opener(opener)
    
                uuids = [k for k in seen if (now - seen[k]).seconds<interval]
                beacon = { 'UUID': uuids, 'Warehouse':"EPE-595" }
                uuid_dump = str.encode(json.dumps(beacon))
                print (uuid_dump)

                try: 
                    req = urllib.request.Request('http://11301770.pxl-ea-ict.be/web/inventory')
                    req.add_header('Content-Type', 'application/json')

                    response = urllib.request.urlopen(req,uuid_dump)
                    lastposted = now
                except URLError:
                    pass 

if __name__ == '__main__':
    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
        print("ble thread started")
    except:
        print("error accessing bluetooth device...")
        sys.exit(1)

    hci_le_set_scan_parameters(sock)
    hci_enable_le_scan(sock)

    try:
        main ()
    finally:
        hci_disable_le_scan (sock)
        sock.close ()
