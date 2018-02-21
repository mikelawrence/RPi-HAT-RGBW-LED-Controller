#!/usr/bin/python3
# Copyright (c) 2018 Mike Lawrence
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from time import sleep
from subprocess import PIPE, Popen
import logging
import threading
import os

from w1thermsensor import W1ThermSensor
from w1thermsensor import NoSensorFoundError

from rgbled import Color, LinearWheel, SineWheel, RgbLed
from timer import InfiniteTimer
from kbhit import KBHit

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))

# Common values
SWEEPTIME = 60          # sweep though all colors in seconds
UPDATERATE = 30         # color updates per second

# Returns the current CPU temperature
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    new = output.decode()
    return new[new.find('=') + 1:new.find("'")]

# Display the CPU and board tempertures on the console.
def measureTemp():
    print("CPU Temp = %sC, HAT Temp %.1fC" % (get_cpu_temperature(),
          boardSensor.get_temperature()))

print("RPi RGBW LED Controller HAT Test")

try:
    # Setup DS18B20 temperature sensor on PCB
    try:
        for curSensor in W1ThermSensor.get_available_sensors(
                [W1ThermSensor.THERM_SENSOR_DS18B20]):
            boardSensor = curSensor

        print("Found 1-Wire temp sensor %s" % (boardSensor.id))
    except NoSensorFoundError:
        boardSensor = None
        print('1-Wire temp sensor not found!')

    print("")
    print("Press any key to exit.")

    # RGB LED controller
    led = RgbLed(freq=200, address=0x40, gamma=1.8)

    # start the background measure temperature timer
    tempTimer = InfiniteTimer(10, measureTemp)
    tempTimer.start()

    # keyboard class
    kb = KBHit()

    # cycle through rainbow colors
    led.on()
    hue = 0.0               # start at red
    exit = False            # don't exit until key is typed
    while not exit:
        led.color = LinearWheel.getrgb(hue)
        sleep(1 / UPDATERATE)
        hue += 360 / (SWEEPTIME * UPDATERATE)
        if hue > 360:
            hue -= 360
        if kb.kbhit():
            exit = True
    print('Exit due to keypress.')
finally:
    tempTimer.cancel()      # stop the background measure temperature timer
    led.off()
