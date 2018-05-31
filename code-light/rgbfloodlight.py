#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#
# Copyright (c) 2018 Mike Lawrence
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import threading
import logging
import os
import sys
import signal
import configparser
import json
from time import sleep
from time import time
from subprocess import PIPE, Popen

from w1thermsensor import W1ThermSensor
from w1thermsensor import NoSensorFoundError
import paho.mqtt.client as mqtt

from timer import InfiniteTimer
from rgbled import RgbLed
from color import Color
import colorwheel

logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))

# User configurable values
FIRMWARE = "0.1.0"
CONFFILE = "rgbfloodlight.conf"
STATEFILE = "rgbfloodlightstate.json"
LEDUPDATERATE = 30                # how often LED is updated (times per second)
SAVEFILEFREQ = 60                 # how long to delay writing to state file
ENABLE_AVAILABILITY_TOPIC = False # enable availability topic

# globals
mqttc = None
led = None

# class to handle SIGTERM signal
class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        self.kill_now = True

# save state to file
def saveStateFile():
    global SaveState
    with open(STATEFILE, 'w') as outfile:
        json.dump(SaveState, outfile)
    print("RGB Floodlight: Updated current state file '%s'." % STATEFILE)

# queue save state to file in order to prevent too frequent writes to Flash
def queueSaveStateFile(state):
    global SaveState, SaveStateTimer

    # try to cancel existing timer
    try:
        SaveStateTimer.cancel()
    except:
        pass
    # keep track of state to save to file
    SaveState = state
    # delay executing save to state file function
    SaveStateTimer = threading.Timer(SAVEFILEFREQ, saveStateFile)
    SaveStateTimer.start()

# publish Hat temperature
def publishTemp():
    mqttc.publish(ConfigHatTemp['state_topic'],
                  payload='{:0.1f}'.format(tempHatMax), qos=1, retain=True)

# Measure the Hat temperture
def measureTemp():
    # use globals to keep track of variables between function calls
    global tempMeasCount, tempHatMax, tempAlarm

    # define variables if they don't exist
    try:
        tempMeasCount
    except NameError:
        tempMeasCount = 0
        tempHatMax = 0.0
        tempAlarm = True        # cause immediate alarm publish

    # get the HAT temperature
    tempHat = hatSensor.get_temperature()
    tempMeasCount += Config.getint('RGB Floodlight', 'Temp_Measurement_Time')
    # keep track of maximum temperature
    if tempHat > tempHatMax:
        tempHatMax = tempHat
    # is it time to publish?
    if tempMeasCount >= Config.getint('RGB Floodlight', 'Temp_Publish_Rate'):
        # time to publish temperatures
        if MqttConnected:
            # We are connected to MQTT broker
            publishTemp()
            tempHatMax = -55.0  # max temp is low so we will catch next high
            tempMeasCount = 0   # start next interval
    # handle over temp alarms
    if tempAlarm:
        # we currently have an over temp situation (add a bit of hysteresis)
        if tempHat < (Config.getfloat('RGB Floodlight', 'Temp_Alarm') - 5.0):
            if MqttConnected:
                # we are connected so publish over temp alarm is now over
                mqttc.publish(ConfigOverTemp['state_topic'],
                              payload=ConfigOverTemp['payload_off'],
                              qos=1, retain=True)
                tempAlarm = False
    else:
        # we currently are in a normal temperature range
        if tempHat >= Config.getfloat('RGB Floodlight', 'Temp_Alarm'):
            if MqttConnected:
                # we are connected so publish over temp alarm
                mqttc.publish(ConfigOverTemp['state_topic'],
                              payload=ConfigOverTemp['payload_on'],
                              qos=1, retain=True)
                tempAlarm = True

# publish the given state
def publishState(state, group=False):
    # prepare a state object to send back to Home Assistant
    color = {'r': state['color'].r,
             'g': state['color'].g,
             'b': state['color'].b}
    if state['state']:
        status = 'ON'
    else:
        status = 'OFF'
    jsonState = {'brightness': state['brightness'],
                 'color': color,
                 'effect': state['effect'],
                 'state': status,
                 'transition': state['transition']
                 }
    # convert to JSON
    payload = json.dumps(jsonState)
    # publish the state
    mqttc.publish(ConfigLight['state_topic'], payload=payload, qos=1,
                  retain=True)
    if (Config.getboolean('Home Assistant', 'Group_Enabled')
        and Config.getboolean('Home Assistant', 'Group_Master')
        and group):
        # group is enabled so publish the state there too
        mqttc.publish(ConfigGroup['state_topic'], payload=payload, qos=1,
                      retain=True)

# handle MQTT message events
def mqtt_on_message(mqttc, obj, msg):
    global NextState, Changed
    if (Config.getboolean('Home Assistant', 'Group_Enabled') and
        msg.topic == ConfigGroup['command_topic'] or
        msg.topic == ConfigLight['command_topic']):
        # received a light command
        payload = msg.payload.decode("utf-8")
        #if msg.topic == ConfigLight['command_topic']:
        #    print("RGB Floodlight: Received command '%s'." % payload)
        #else:
        #    print("RGB Floodlight: Received group command '%s'." % payload)
        try:
            command = json.loads(payload)
        except ValueError:
            print("RGB Floodlight: JSON failed to decode command '%s'."
                  % payload)
            return
        cmdStateChanged = False
        if 'brightness' in command:
            newBrightness = command['brightness']
            if CurState['brightness'] != newBrightness:
                NextState['brightness'] = newBrightness
                cmdStateChanged = True
                #print("RGB Floodlight: Brightness was changed to %d."
                #      % newBrightness)
        elif 'color' in command:
            newColor = Color(command['color']['r'], command['color']['g'],
                             command['color']['b'])
            if CurState['color'] != newColor:
                NextState['color'] = newColor
                cmdStateChanged = True
                #print("RGB Floodlight: Color was changed to Color(%s)."
                #      % str(newColor))
        elif 'effect' in command:
            newEffect = command['effect']
            if newEffect not in colorwheel.getcolorwheellist():
                print("RGB Floodlight: Commanded effect '%s' is not a "
                      "valid effect." % newEffect)
            else:
                if CurState['effect'] != newEffect:
                    NextState['effect'] = newEffect
                    cmdStateChanged = True
                    #print("RGB Floodlight: Effect was changed to '%s'."
                    #      % newEffect)
        elif 'state' in command:
            newState = command['state'].lower() == 'on'
            if CurState['state'] != newState:
                NextState['state'] = newState
                cmdStateChanged = True
                #if newState:
                #    print("RGB Floodlight: Light was turned ON.")
                #else:
                #    print("RGB Floodlight: Light was turned OFF.")
        elif 'transition' in command:
            newTransition = command['transition']
            if CurState['transition'] != newTransition:
                NextState['transition'] = newTransition
                cmdStateChanged = True
                #print("RGB Floodlight: Transition was changed to %d."
                #      % newTransition)

        # publish the current state new or not
        publishState(NextState, msg.topic == ConfigGroup['command_topic'])
        # indicate when parameters have been changed to rest of program
        if cmdStateChanged:
            Changed = True
            queueSaveStateFile(NextState)
        #print("RGB Floodlight: New state '%s'." % payload)
    else:
        print("RGB Floodlight: Received unknown command topic '%s', with "
              "payload '%s'." % (msg.topic, msg.payload.decode("utf-8")))


# handle MQTT connection events
def mqtt_on_connect(mqttc, userdata, flags, rc):
    global MqttConnected
    if rc == 0:
        # connection was successful
        MqttConnected = True
        print("RGB Floodlight: Connected to broker: mqtt://%s:%d"
              % (mqttc._host, mqttc._port))
        # publish node configs is discovery is on
        if Config.getboolean('Home Assistant', 'Discovery_Enabled'):
            # discovery is enabled so publish config data
            mqttc.publish(str("/".join([TopicLight, 'config'])),
                          payload=json.dumps(ConfigLight), qos=1,
                          retain=True)
            mqttc.publish(str("/".join([TopicHatTemp, 'config'])),
                          payload=json.dumps(ConfigHatTemp), qos=1,
                          retain=True)
            mqttc.publish(str("/".join([TopicOverTemp, 'config'])),
                          payload=json.dumps(ConfigOverTemp), qos=1,
                          retain=True)
        else:
            # discovery is disabled so publish blank config
            mqttc.publish(str("/".join([TopicLight, 'config'])),
                          payload="", qos=1, retain=True)
            mqttc.publish(str("/".join([TopicHatTemp, 'config'])),
                          payload="", qos=1, retain=True)
            mqttc.publish(str("/".join([TopicOverTemp, 'config'])),
                          payload="", qos=1, retain=True)
        # publish group configs
        if (Config.getboolean('Home Assistant', 'Discovery_Enabled')
            and Config.getboolean('Home Assistant', 'Group_Enabled')
            and Config.getboolean('Home Assistant', 'Group_Master')):
           # discovery and groups are enabled so publish group config data
            mqttc.publish(str("/".join([TopicGroup, 'config'])),
                          payload=json.dumps(ConfigGroup), qos=1,
                          retain=True)
        else:
            # discovery and groups are disabled so publish blank config
            mqttc.publish(str("/".join([TopicGroup, 'config'])),
                          payload="", qos=1, retain=True)
        # indicate we are online now
        mqttc.publish(availability_topic,
                      payload=payload_available,
                      qos=1, retain=True)
        # subscribe to json light command topic
        mqttc.subscribe(ConfigLight['command_topic'])
        # subscribe to group json light command topic
        if Config.getboolean('Home Assistant', 'Group_Enabled'):
            # group is enabled so listen for commands on group command topic
            mqttc.subscribe(ConfigGroup['command_topic'])
    else:
        # connection failed
        print("RGB Floodlight: MQTT_ERR=%d: Failed to connect to broker: "
              "mqtt://%s:%d " % (rc, mqttc._host, mqttc._port))

# handle MQTT disconnect events
def mqtt_on_disconnect(client, userdata, rc):
    global MqttConnected
    MqttConnected = False

def mqtt_subscribe():
    pass

try:
    # load config file
    if not os.path.isfile(CONFFILE):
        sys.exit("RGB Floodlight: '%s' config file is missing." % CONFFILE)
    Config = configparser.ConfigParser(
        defaults = {
            'MQTT': {
                'Broker': '127.0.0.1',
                'Port': '1883',
                'KeepAlive': '60'
            },
            'Home Assistant': {
                'Discovery_Enabled': 'false',
                'Discovery_Prefix': 'homeassistant',
                'Node_ID': 'default_node_id',
                'Node_Name': 'Default Node Name',
                'Group_Enabled': 'false',
                'Group_Master': 'false',
                'Group_ID': 'default_group_id',
                'Group_Name': 'Default Group Name'
            },
            'RGB Floodlight': {
                'Temp_Measurement_Time': '10',
                'Temp_Publish_Rate': '300',
                'Temp_Alarm': '85.0'
            }
        })
    Config.read(CONFFILE)

    # load current state file
    try:
        with open(STATEFILE, 'r') as infile:
            CurState = json.load(infile)
        CurState['color'] = Color(CurState['color'][0],
                                  CurState['color'][1],
                                  CurState['color'][2])
        print("RGB Floodlight: Loaded state file '%s'." % STATEFILE)
    except:
        # load defaults if there is an exception in loading the state file
        print("RGB Floodlight: Failed to load state file '%s'." % STATEFILE)
        CurState = {
            'brightness': 255,
            'color': Color(255,0,255),
            'effect': 'Primary Blend',
            'state': True,
            'transition': 120,
        }
        queueSaveStateFile(CurState)
    NextState = CurState
    Changed = True

    # create RGB Floodlight Device Home Assistant Discovery Config
    TopicLight = str(
        "/".join([Config.get('Home Assistant', 'Discovery_Prefix'), 'light',
        Config.get('Home Assistant', 'Node_ID'), 'rgblight']))
    ConfigLight = {
        'name': Config.get('Home Assistant', 'Node_Name'),
        'platform': 'mqtt_json',
        'brightness': True,
        'rgb': True,
        'effect': True,
        'state_topic': str("/".join([TopicLight, 'state'])),
        'command_topic': str("/".join([TopicLight, 'set'])),
        'brightness_scale': 255,
        'effect_list': colorwheel.getcolorwheellist(),
        'retain': True,
        'qos': 1,
    }
    # generate availability strings
    availability_topic = str("/".join([TopicLight, 'status']))
    payload_available = 'online'
    payload_not_available = 'offline'
    # add availability topic if configured
    if ENABLE_AVAILABILITY_TOPIC == True:
        ConfigLight['availability_topic'] = availability_topic
        ConfigLight['payload_available'] = payload_available
        ConfigLight['payload_not_available'] = payload_not_available

    # create RGB Floodlight Group Device Home Assistant Discovery Config
    TopicGroup = str(
        "/".join([Config.get('Home Assistant', 'Discovery_Prefix'), 'light',
        Config.get('Home Assistant', 'Group_ID'), 'rgblight']))
    ConfigGroup = {
        'name': Config.get('Home Assistant', 'Group_Name'),
        'platform': 'mqtt_json',
        'brightness': True,
        'rgb': True,
        'effect': True,
        'state_topic': str("/".join([TopicGroup, 'state'])),
        'command_topic': str("/".join([TopicGroup, 'set'])),
        'brightness_scale': 255,
        'effect_list': colorwheel.getcolorwheellist(),
        'retain': True,
        'qos': 1,
    }

    # create HAT Temperature Device Home Assistant Discovery Config
    TopicHatTemp = str(
        "/".join([Config.get('Home Assistant', 'Discovery_Prefix'), 'sensor',
        Config.get('Home Assistant', 'Node_ID'), 'temperature']))
    ConfigHatTemp = {
        'name': Config.get('Home Assistant', 'Node_Name') + " Temperature",
        'state_topic': str("/".join([TopicHatTemp, 'state'])),
        'unit_of_measurement': '°C',
    }

    # create Over Temp Alarm Device Home Assistant Discovery Config
    TopicOverTemp = str(
        "/".join([Config.get('Home Assistant', 'Discovery_Prefix'),
        'binary_sensor', Config.get('Home Assistant', 'Node_ID'),
        'over_temperature']))
    ConfigOverTemp = {
        'name': Config.get('Home Assistant', 'Node_Name')
                + " Over Temperature Alarm",
        'state_topic': str("/".join([TopicOverTemp, 'state'])),
        'device_class': 'heat',
        'payload_on': 'ON',
        'payload_off': 'OFF',
    }

    # setup MQTT
    mqttc = mqtt.Client()
    mqttc.on_message = mqtt_on_message
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_disconnect = mqtt_on_disconnect
    mqttc.will_set(availability_topic,
                   payload=payload_not_available,
                   retain=False)
    mqttc.connect(Config.get('MQTT', 'Broker'),
                  port=Config.getint('MQTT', 'Port'),
                  keepalive=Config.getint('MQTT', 'KeepAlive'))
    mqttc.loop_start()

    # RGB LED controller
    led = RgbLed(freq=200, address=0x40, gamma=1.8,
                 scaleR=1.0, scaleG=0.75, scaleB=1.0)

    # Setup DS18B20 temperature sensor on PCB
    try:
        for curSensor in W1ThermSensor.get_available_sensors(
                [W1ThermSensor.THERM_SENSOR_DS18B20]):
            hatSensor = curSensor
    except NoSensorFoundError:
        hatSensor = None
        print("RGB Floodlight: HAT 1-Wire temperature sensor not found!")

    # publish temps now
    measureTemp()
    publishTemp()

    # start the background measure temperature timer
    tempTimer = InfiniteTimer(
        Config.getint('RGB Floodlight', 'Temp_Measurement_Time'),
        measureTemp, name="TempTimer")
    tempTimer.start()

    # grab SIGTERM to shutdown gracefully
    killer = GracefulKiller()

    # cycle through rainbow colors
    led.on()

    # setup color based on last state
    while True:
        # handle switch to new state
        if Changed:
            # determine what changed
            changes = []
            if (CurState['state'] != NextState['state']):
                if NextState['state']:
                    changes.append("State=On")
                else:
                    changes.append("State=Off")
            if (CurState['brightness'] != NextState['brightness']):
                changes.append("Brightness=%d" % NextState['brightness'])
            if (CurState['color'] != NextState['color']):
                changes.append('Color=(%s)' % str(NextState['color']))
            if (CurState['effect'] != NextState['effect']):
                changes.append('Effect="%s"' % NextState['effect'])
            if (CurState['transition'] != NextState['transition']):
                changes.append("Transition=%d" % NextState['transition'])
            if len(changes) > 0:
                # something Changed
                print("RGB Floodlight: State changed to %s."
                      % str(", ".join(changes)))
            # next state is now current state
            CurState = dict(NextState)
            # no longer changed
            Changed = False
            # restart angle
            angle = 0.0
            # select the correct color wheel from effect and color
            wheel = colorwheel.getcolorwheelfromname(CurState['effect'],
                                                     CurState['color'])
            # LED update rate in seconds
            ledDelayTime = 1 / LEDUPDATERATE
            # used to align transition time
            startTime = time()
            # adjust the LED brightness
            led.brightness = CurState['brightness']
            # adjust the LED ON state
            led.set(is_on=CurState['state'])
        # get next the color
        led.color = wheel.getrgb(angle)
        # sleep the correct amount of time to meet the specified period
        sleep(ledDelayTime - ((time() - startTime) % ledDelayTime))
        # increment the angle by the step amount
        angle += 360 / (CurState['transition'] * LEDUPDATERATE)
        # prevent angle from exceeding 360 (not really necessary)
        if angle > 360:
            angle -= 360
        #print("RGB Floodlight: Angle = %.2f, Color=(%s)." %
        #    (angle, led.color))
        # did we receive a signal to exit?
        if killer.kill_now:
            break
finally:
    # shutdown MQTT gracefully
    if mqttc is not None:
        # set will for offline status
        mqttc.publish(availability_topic,
                      payload=payload_not_available,
                      qos=1, retain=True)
        mqttc.loop_stop()
        mqttc.disconnect()  # disconnect from MQTT broker
        print("RGB Floodlight: Disconnecting from broker: mqtt://%s:%d"
              % (mqttc._host, mqttc._port))
    # try to cancel existing save state file timer
    try:
        SaveStateTimer.cancel()
    except:
        pass
    # We want LED off when this program is not running
    if led is not None:
        led.off()           # turn off the Light
