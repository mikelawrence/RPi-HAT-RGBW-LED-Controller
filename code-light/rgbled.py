# -*- coding: UTF-8 -*-
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
from PCA9685 import PCA9685
from color import Color
import logging

# Common Values
GAMMA       = 1.8

# logger for this module
logger = logging.getLogger(__name__)

"""RGB led controller through PCA9685 PWM IC."""
class RgbLed:
    def __init__(self, freq=200, address=0x40, gamma=1.0,
                 scaleR=1.0, scaleG=1.0, scaleB=1.0):
        """
        Initialize the driver.

        :param freq: The pwm frequency.
        :param address: The address of the PCA9685.
        :param gamma: Gamma value used for gamma correction.
                      A value of 1 means no correction.
        """
        self._device = PCA9685(address)
        logger.debug("Setting PCA9685 address to 0x%02x" % (address))
        self._device.set_pwm_freq(freq)
        self._gamma = gamma
        self._color = Color(0,0,0)
        self._is_on = False
        self._brightness = 1.0
        self._scaleR = scaleR
        self._scaleG = scaleG
        self._scaleB = scaleB

    def on(self):
        """Turn the led on."""
        self.set(is_on=True)

    def off(self):
        """Turn the led off."""
        self.set(is_on=False)

    @property
    def color(self):
        """
        The color property.

        :return: The color of the led.
        """
        return self._color

    @color.setter
    def color(self, color):
        """
        Set the color of the led updating pwm values.

        :param color: Color of the led.
        """
        self.set(color=color)

    @property
    def brightness(self):
        """
        The brightness property.

        :return: The brightness of the led.
        """
        return self._brightness

    @color.setter
    def brightness(self, brightness):
        """
        Set the brightness of the led updating pwm values.

        :param color: Brightness of the led.
        """
        self.set(brightness=brightness)

    def set(self, is_on=None, brightness=None, color=None):
        """
        Set properties of the led simultaneously before updating pwm values.

        :param is_on: On-off state of the led.
        :param brightness: Brightness of the led.
        :param color: Color of the led.
        """
        if color is not None:
            self._color = color
        if brightness is not None:
            self._brightness = brightness
        if is_on is not None:
            self._is_on = is_on

        # time to update the pwm Values
        self._set_pwm()

    def _set_pwm(self):
        """
        Set pwm values for current settings.
        """
        # adjust color brightness
        color = Color(self._color.r * self._brightness / 255,
                      self._color.g * self._brightness / 255,
                      self._color.b * self._brightness / 255)
        # pwm goes to 0% if led is not on
        if not self._is_on:
            color = Color(0,0,0)
        # gamma correction?
        if self._gamma != 1.0:
            # gamma correction with output sized for 12-bit pwm
            pwmValues = color.gamma(gamma=GAMMA, max=4095)
        else:
            # size output for 12-bit pmw with NO gamma correction
            pwmValues = [(x * 4096 / 255) for x in color]
        # scale pwm values based on scale factors
        pwmValues[0] = round(pwmValues[0] * self._scaleR)
        pwmValues[1] = round(pwmValues[1] * self._scaleG)
        pwmValues[2] = round(pwmValues[2] * self._scaleB)
        # finally set the pwm values
        self._device.set_multiple_pwm(pwmValues)
        #print("R=%d, G=%d, B=%d"% (pwmValues[0], pwmValues[1], pwmValues[2]))
