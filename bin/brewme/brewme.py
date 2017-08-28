#!/usr/bin/env python

import csv
import datetime
import glob
import os
import random
import socket
import subprocess
import sys
import time


# ##############################
# Constants
#

# OUTPUT_MODE
#   Sets the reporting method for recording temperatures.
# Values:
#   'carbon':       Write temperatures directly to Carbon Cache over TCP socket
#   'carbon-debug': Write carbon-formatted messages to STDOUT instead of a TCP socket
#   'collectd':     Record temperatures to STDOUT and assume that a collectd
#                   daemon is monitoring output and recording results
OUTPUT_MODE = 'carbon-debug'

# SIMULATE_GPIO
#   For testing, this flag can be set to true to simulate all
#   GPIO interactions.  For example, random numbers will be
#   returned instead of reading actual devices, etc.
SIMULATE_GPIO = True

# HOSTNAME
#   Hostname of the machine collecting metrics to be used in reporting
HOSTNAME = os.environ.get('HOSTNAME', subprocess.check_output(['hostname', '-f']).strip())

# INTERVAL
#   Reporting interval in seconds between each round of metrics collection.
INTERVAL = 5

# DEVICES
#   Mapping of user-readable names to system GPIO device locations from which
#   temperatures can be read on the Raspberry Pi
DEVICES = {
    'wort': '/sys/bus/w1/devices/28-0416a45a40ff/w1_slave',
    'ambient': '/sys/bus/w1/devices/28-0516a44741ff/w1_slave',
    'bath': '/sys/bus/w1/devices/28-0416a29494ff/w1_slave',
    'chest': '/sys/bus/w1/devices/28-0316a36a56ff/w1_slave',
}

# CARBON_SERVER and CARBON_PORT
#   Location of the carbon-cache server for the 'graphite' and 'carbon'
#   output modes.  These only have to be set for those output modes.
CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003

# LED_PIN
#   GPIO pin number that the LED light switch is on
LED_PIN = 17

# ON and OFF
#   Constants to make some operations below more readable
ON = True
OFF = False


# ##############################
# Functions
#

def read_rawtemp(device):
    with open(device, 'r') as f:
        return f.readlines()

def switch_led(on):
    if not SIMULATE_GPIO:
        GPIO.output(LED_PIN, bool(on))

def read_temp(device):
    # Simulations will return a random float between 65 and 75
    if SIMULATE_GPIO:
        return 65 + random.random() * 10
    # Otherwise, read the actual temperature from the filesystem
    lines = read_rawtemp(device)
    while lines[0].strip()[-3:] !='YES':
        time.sleep(0.2)
        lines = read_rawtemp(device)
    equals_pos = lines[1].find('t=')
    if equals_pos !=-1:
        temp_string = lines[1][equals_pos+2:]
        temp = float(temp_string)/1000.0
        temp_F = temp * 9 / 5 + 32
        return temp_F

def flash_led(seconds=1, times=1):
    switch_led(OFF)
    first=True
    for i in range(times):
        # If there is more than one flash, pause in between
        if not first:
            time.sleep(seconds)
        first=False
        # Turn on, wait, turn off
        switch_led(ON)
        time.sleep(seconds)
        switch_led(OFF)

def init_gpio():
    if SIMULATE_GPIO:
        return
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setwarnings(False)
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

def cleanup(*args, **kwargs):
    if not SIMULATE_GPIO:
        GPIO.cleanup()
    sys.exit(0)

def record_temp(device, temp):
    if OUTPUT_MODE == 'collectd':
        sys.stdout.write('PUTVAL "{0}/brewme-{1}/gauge-temperature" interval={2} {3}:{4}\n' \
                         .format(HOSTNAME, name, INTERVAL, time.time(), temp))
    elif OUTPUT_MODE == 'carbon' or OUTPUT_MODE == 'carbon-debug':
        msg = 'brewme.{0}.{1}.temperature {2} {3}\n'.format(HOSTNAME, device, temp, time.time())
        if OUTPUT_MODE == 'carbon':
            sock = socket.socket()
            sock.connect((CARBON_SERVER, CARBON_PORT))
            sock.sendall(msg)
            sock.close()
        else:
            sys.stdout.write(msg)
    else:
        raise ValueError("Illegal value set for OUTPUT_MODE: {0}".format(OUTPUT_MODE))

# ##############################
# Main Program
#

# If GPIO is enabled, import the libraries
if not SIMULATE_GPIO:
    try:
        import RPi.GPIO as GPIO
    except ImportError as e:
        raise ImportError('{0}.\n--> Are you running this on a Raspberry Pi? '.format(e) + \
                          'If not, set SIMULATE_GPIO to True for testing.')


try:
    # Initialize Devices
    if SIMULATE_GPIO:
        sys.stderr.write('GPIO disabled; all temperature readings will be simulated\n')
    else:
        sys.stderr.write('Initializing GPIO drivers...\n')
        init_gpio()
        sys.stderr.write('GPIO Initialized\n')

    # Flash the LED to indicate startup
    flash_led(seconds=0.5, times=3)

    # Start the runloop
    sys.stderr.write('Beginning temperature collection...\n')
    while True:
        # Turn on the LED when we start a processing round
        switch_led(ON)
        roundStart = time.time()
        # Record the temperature from each device
        for name, device in DEVICES.items():
            record_temp(name, read_temp(device))
        # Shut off the LED and wait until the reporting interval
        # expires before starting next round
        switch_led(OFF)
        while time.time() - roundStart < INTERVAL:
            time.sleep(0.1)
finally:
    sys.stderr.write('Shutting down...\n')
    cleanup()
