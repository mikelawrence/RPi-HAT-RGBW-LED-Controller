# RGB Floodlight Application
The RGB Floodlight application is written in Python 3 and supports the RGB hardware elements of the RGBW LED Controller HAT which in turn drives a 50W RGB Floodlight. The application is also a discoverable light for [Home Assistant](https://home-assistant.io/), an open-source home automation platform running on Python 3. [MQTT](http://mqtt.org/), a machine-to-machine (M2M)/"Internet of Things" connectivity protocol, is the basis of communication with Home Assistant.

All settings for this application are in the '[rgbfloodlight.conf](rgbfloodlight.conf)'. This is where you point to the correct MQTT broker and configure how the light works. There are a few settings of note here. Discovery_Enabled = false will prevent Home Assistant from automatically discovering the light. Group_Enable = true adds a second MQTT light to Home Assistant that supports multiple RGB Floodlights. Each light that has the same Group_ID will respond state changes in unison. Be sure to set Group_Master = true for only one light in a group.

If you don't want to use discovery here is the configuration of the light in Home Assistant. Note the 'Studio-Roof-Floodlight' you see in the example yaml is the Node_ID which is specified in the 'rgbfloodlight.conf' file. The light platform for Home Assistant is [MQTT JSON Light](https://home-assistant.io/components/light.mqtt_json/) configured with RGB and brightness support. The RGB Floodlight also reports internal temperature (platform [MQTT Sensor](https://home-assistant.io/components/sensor.mqtt/)) and an over temperature alarm (platform [MQTT Binary_Sensor](https://home-assistant.io/components/binary_sensor.mqtt/))
```yaml
# Example configuration.yaml entry
light:
  # Main RGB Floodlight config
  - platform: mqtt_json
    name: Studio Roof RGB Floodlight
    state_topic: "hass/light/Studio-Roof-Floodlight/rgblight/state"
    command_topic: "hass/light/Studio-Roof-Floodlight/rgblight/set"
    brightness: true
    rgb: true
    effect: true
    qos: 1
    retain: true
    brightness_scale: 255
    effect_list:
      - Single Color
      - Single Color Bounce
      - Primary Bounce
      - Primary Blend
      - Rainbow Bounce
      - Rainbow Blend
      - Christmas
      - Halloween
    availability_topic: "hass/light/Studio-Roof-Floodlight/rgblight/status"
    payload_available: "online"
    payload_not_available: "offline"

  # Group RGB Floodlight config
  - platform: mqtt_json
    name: Roof RGB Floodlights
    state_topic: "hass/light/Roof-Floodlights/rgblight/state"
    command_topic: "hass/light/Roof-Floodlights/rgblight/set"
    brightness: true
    rgb: true
    effect: true
    qos: 1
    retain: true
    brightness_scale: 255
    effect_list:
      - Single Color
      - Single Color Bounce
      - Primary Bounce
      - Primary Blend
      - Rainbow Bounce
      - Rainbow Blend
      - Christmas
      - Halloween

sensor:
  - platform: mqtt
    name: Studio Roof RGB Floodlight Temperature
    state_topic: "hass/sensor/Studio-Roof-Floodlight/temperature/state"
    unit_of_measurement: "°C"

binary_sensor:
  - platform: mqtt
    name: Studio Roof RGB Floodlight Over Temperature Alarm
    state_topic: "hass/sensor/Studio-Roof-Floodlight/hat_temperature/state"
    device_class: "heat"
    payload_on: "ON"
    payload_off: "OFF"
```
The RGB Floodlight subscribes to the command_topic and expects JSON control data in the following format...

```JSON
{
  "brightness": 255,
  "color": {
    "r": 255,
    "g": 255,
    "b": 255
  },
  "effect": "Single Color",
  "state": "ON",
  "transition": 120
}
```
Note the "transition" parameter specifies how long a given effect last before repeating and is not part of the Home Assistant light control so an additional control and automation is required see below..
```yaml
# Input slider for transition time
input_number:
  studio_floodlight_transition_time:
    name: "Studio Roof Floodlight Transition Speed"
    initial: 120
    min: 1
    max: 180
    step: 1
# automation to pipe the transition value over to light
automation:
  - id: studio_roof_transition_speed
    alias: "Studio Roof Floodlight Transition Speed"
    initial_state: True
    hide_entity: False
    trigger:
      - platform: state
        entity_id: input_number.studio_floodlight_transition_time
    action:
      - service: mqtt.publish
        data_template:
          topic: "hass/light/Studio-Roof-Floodlight/rgblight/set"
          payload: '{"transition": {{ trigger.to_state.state | int }}}'

```
## Other Software Notes
The PCA9685 driver is based on Adafruit's Python PCA9685 library (PCA9685.py). While this library works it had some problems. First every register write is a single 8-bit I<sup>2</sup>C transaction even for those registers like LEDn_ON which are actually two 8-bit registers together. So I changed all multi-register writes to support the writeList() method which writes multiple bytes from a starting address in a single transaction. This required also setting the AI bit in the MODE1 register which configures the PCA9685 to auto-increment the address counter on I<sup>2</sup>C transactions. Finally I added a method, set_multiple_pwm(), that writes the LED On and LED Off values for multiple PWM channels starting with CH0. This allows the RGB PWM values to be updated simultaneously.

The rgbled.py file provides all of the RGB LED control through the PCA9685 PWM controller. Once initialized use the set() method to change color and brightness which in turn will compute appropriate PWM values and send them to the PCA9685.

The Color class is defined in the color.py file. Color is defined as a tuple representing a color using Red, Green, and Blue values with a range of [0:255]. This class defines the blend() method used to linearly blend from one color to the next. Gamma correction is provided by the gamma() method.

The colorwheel.py file is a set of classes that provide a convenient method of converting an angle with the range [0:360] to a color that is either a blend between multiple colors or a bounce effect of fading out one color before switching to another. Multiple colorwheel classes are defined as effects. For instance there is the PrimaryBlendWheel which blends between the primary colors. Or the RainbowBounceWheel which fades between colors of the Rainbow.

## Raspberry Pi Setup
This setup makes two key assumptions. First you are using Raspbian. Second, Python 3 is the target programming environment. Install or update Python3 and necessary libraries by performing the following...
```
sudo apt-get update
sudo apt-get -y install python3-dev python3-pip git paho-mqtt python3-w1thermsensor
pip3 install Adafruit-GPIO paho-mqtt
```
It is also assumed that you already cloned this repository as shown in the main project [README file](../README.md). Be sure to edit the 'rgbfloodlight.conf' file to support your configuration. Test the software by executing the following commands.
```
cd ~/projects/RPi-HAT-RGBW-LED-Controller/code-light/
chmod 755 rgbfloddlight.py
./rgbfloodlight.py
```
If you see no errors you should be able to see your light in Home Assistant. Configuring Home Assistant is a bit of a stretch for guide but here are a couple of hints.

* Make sure you have a working MQTT configuration. If you use HASS.IO goto the HASS.IO configuration and install the Mosquitto Broker.
* Make sure you have MQTT discovery enabled. See [MQTT Discovery](https://home-assistant.io/docs/mqtt/discovery/).
* Make sure your MQTT discovery prefix matches the Discovery_Prefix in your RGB Floodlight configuration file. See [MQTT Discovery](https://home-assistant.io/docs/mqtt/discovery/).

I use HASS.IO with the Mosquitto Broker addon installed and my configuration for MQTT is as follows...
```yaml
mqtt:
  broker: core-mosquitto
  discovery: true
  discovery_prefix: hass

```
## Systemd run at boot
To make this code run at boot enter the following commands...
```
cd ~/projects/RPi-HAT-RGBW-LED-Controller/code-light
sudo cp rgbfloodlight.service /lib/systemd/system
sudo systemctl enable rgbfloodlight.service
sudo systemctl start rgbfloodlight.service
```

# Acknowledgments
The following python libraries are required.
* [Eclipse Paho™ MQTT Python Client](https://github.com/eclipse/paho.mqtt.python)
* [Python3 w1thermsensor](https://github.com/timofurrer/w1thermsensor)
* [Adafruit Python GPIO](https://github.com/adafruit/Adafruit_Python_GPIO)

The following library is used but was modified so included in this repository.
* [Adafruit Python PCA9685](https://github.com/adafruit/Adafruit_Python_PCA9685).

The following code was pulled from the Internet
* [kbhit.py](http://home.wlu.edu/~levys/software/kbhit.py) from Simon D. Levy
* [timer.py](https://github.com/jalmeroth/homie-python/blob/master/homie/timer.py)

 I want to thank Jan Almeroth for [homie-python](https://github.com/jalmeroth/homie-python/blob/master/homie/timer.py) which is a Python implementation of the Homie MQTT convention. While I ended up not using Homie it showed me how to use the Paho MQTT Python Client.
