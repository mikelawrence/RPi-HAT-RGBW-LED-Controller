"""RGB led controller through PCA9685 PWM IC."""

from PCA9685 import PCA9685
from collections import namedtuple
import math
import logging

# Common Values
GAMMA       = 1.8

# logger for this module
logger = logging.getLogger(__name__)

""" RBG Color tuple definition. """
Color = namedtuple('Color', 'R G B')

""" Performs gamma correction on RGB color. """
def GammaCorrection(color, gamma=2.8, max=255):
    """
    Perfomes Gamma Correction on a color.

    :param color: The color to perform the gamma correction on.
    :param gamma: The gamma value.
    :param max: Specifies full scale output of the gamma correction.

    :return: Gamma corrected color.
    """
    return [round(max * ((x / 255) ** gamma)) for x in color]

class ColorWheel:
    """Base class for Color Wheel. Cannot be used directly. """
    def getrgb(hue):
        """
        Method stub for getting an RGB color from Hue.

        Has to be implemented by inheriting classes.
        :param hue: Hue range 0 - 360.

        :return: Returns RGB color for specified hue.
        """
        raise NotImplementedError

class LinearWheel(ColorWheel):
    def getrgb(hue):
        """
        Get linear RGB color from Hue.

        :param hue: Hue range 0 - 360.

        :return: Returns RGB color for specified hue.
        """
        # force hue into range
        angle = hue % 360
        if angle < 0:
            angle += 360

        # get colors based on angle
        if angle < 60:
            red = 255
            green = round(angle * 4.25)
            blue = 0
        elif angle < 120:
            red = round((120 - angle) * 4.25)
            green = 255
            blue = 0
        elif angle < 180:
            red = 0
            green = 255
            blue = round((angle - 120) * 4.25)
        elif angle < 240:
            red = 0
            green = round((240 - angle) * 4.25)
            blue = 255
        elif angle < 300:
            red = round((angle - 240) * 4.25)
            green = 0
            blue = 255
        else:
            red = 255
            green = 0
            blue = round((360 - angle) * 4.25)

        return Color(red, green, blue)

class SineWheel(ColorWheel):
    def getrgb(hue):
        """
        Get sine wave RGB color from Hue.

        :param hue: Hue range 0 - 360.

        :return: Returns RGB color for specified hue.
        """
        # force hue into range
        angle = hue % 360
        if angle < 0:
            angle += 360
        scale = 255 / 2

        # get colors based on angle, red first
        if angle < 120:
            red = round((math.cos(math.radians(angle * 1.5)) + 1) * scale)
        elif angle >= 240:
            red = round((1 - math.cos(math.radians((angle - 240) * 1.5))) * scale)
        else:
            red = 0
        # handle green
        if angle < 240:
            green = round((1 - math.cos(math.radians(angle * 1.5))) * scale)
        else:
            green = 0
        # handle blue
        if angle < 120:
            blue = 0
        else:
            blue = round((1 - math.cos(math.radians((angle - 120) * 1.5))) * scale)

        return Color(red, green, blue)

class RgbLed:
    def __init__(self, freq=200, address=0x40, gamma=1.0):
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
        self._brightness = 1
        self._is_on = False

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
        Brightness property.

        :return: The brightness of the led (0.0-1.0).
        """
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        """
        Set the brightness of the led.

        :param brightness: The brightness to set (0.0-1.0).
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
        color = self._color
        # pwm goes to 0% if led is not on
        if not self._is_on:
            color = Color(0,0,0)
        # adjust for Brightness
        color = color * self._brightness
        # gamma correction?
        if self._gamma != 1.0:
            # gamma correction with output sized for 12-bit pwm
            color = GammaCorrection(color, gamma=self._gamma, max=4095)
        else:
            # size output for 12-bit pmw with NO gamma correction
            color = [(x * 4096 / 255) for x in color]
        # finally set the pwm values
        self._device.set_multiple_pwm(color)
