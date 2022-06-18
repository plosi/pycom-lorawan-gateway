from network import WLAN
import time
import machine
from machine import RTC
import pycom
from _secrets import known_nets


"""
TO DO: wifi manager to add new known networks on the go
"""

print('\nStarting LoRaWAN concentrator')
# Disable Hearbeat
pycom.heartbeat(False)

# Define callback function for Pygate events
def machine_cb (arg):
    evt = machine.events()
    if (evt & machine.PYGATE_START_EVT):
        # Green
        pycom.rgbled(0x103300)
    elif (evt & machine.PYGATE_ERROR_EVT):
        # Red
        pycom.rgbled(0x331000)
    elif (evt & machine.PYGATE_STOP_EVT):
        # RGB off
        pycom.rgbled(0x000000)

# register callback function
machine.callback(trigger = (machine.PYGATE_START_EVT | machine.PYGATE_STOP_EVT | machine.PYGATE_ERROR_EVT), handler=machine_cb)

# Scan for known wifi networks and connect to wifi
def _connect_to_wifi():
    available_nets = wlan.scan()
    nets = frozenset([e.ssid for e in available_nets])
    known_nets_names = frozenset([key for key in known_nets])
    net_to_use = list(nets & known_nets_names)

    net_to_use = net_to_use[0]

    net_properties = known_nets[net_to_use]
    pwd = net_properties['pwd']
    sec = [e.sec for e in available_nets if e.ssid == net_to_use][0]
    if 'wlan_config' in net_properties:
        wlan.ifconfig(config=net_properties['wlan_config'])
    wlan.connect(net_to_use, (sec, pwd))
    while not wlan.isconnected():
        time.sleep_ms(50)
    print('WiFi connected to: ', net_to_use)

print('Connecting to WiFi...',  end='')
# Connect to a Wifi Network
wlan = WLAN(mode=WLAN.STA)
_connect_to_wifi()
#wlan.connect(ssid=SSID, auth=(WLAN.WPA2, WIFI_PASSWORD))

while not wlan.isconnected():
    print('.', end='')
    time.sleep(1)
print(" OK")

# Sync time via NTP server for GW timestamps on Events
print('Syncing RTC via ntp...', end='')
rtc = RTC()
rtc.ntp_sync(server="pool.ntp.org")

while not rtc.synced():
    print('.', end='')
    time.sleep(.5)
print(" OK\n")

# Read the GW config file from Filesystem
with open('/flash/config.json','r') as fp:
    buf = fp.read()

# Start the Pygate
machine.pygate_init(buf)
# disable degub messages
# machine.pygate_debug_level(1)