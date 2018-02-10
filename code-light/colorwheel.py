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
#
from color import Color
import color
import math
import logging

# logger for this module
logger = logging.getLogger(__name__)

WheelList = ['Single Color', 'Single Color Bounce', 'Primary Bounce', 'Primary Blend', 'Rainbow Bounce', 'Rainbow Blend', 'Christmas', 'Halloween']

def getcolorwheellist():
    """Gets a list of color wheel names."""
    return WheelList

def getcolorwheelfromname(name, color):
    """Gets an initialized ColorWheel from name and color."""
    if name not in WheelList:
        raise ValueError("Name is not a valid ColorWheel")

    if name == WheelList[0]:
        # Single Color
        return ColorBlendWheel([color])
    if name == WheelList[1]:
        # Single Color Bounce
        return ColorBounceWheel([color, color])
    if name == WheelList[2]:
        # Primary Bounce
        return PrimaryBounceWheel()
    if name == WheelList[3]:
        # Primary Blend
        return PrimaryBlendWheel()
    if name == WheelList[4]:
        # Rainbow Bounce
        return RainbowBounceWheel()
    if name == WheelList[5]:
        # Rainbow Blend
        return RainbowBlendWheel()
    if name == WheelList[6]:
        # Christmas
        return ChristmasBounceWheel()
    if name == WheelList[7]:
        # Halloween
        return HalloweenBounceWheel()

class ColorWheel:
    """Base class for Color Wheel. Cannot be used directly. """
    def getrgb(self, angle):
        """
        Method stub for getting an RGB color from an angle.

        Has to be implemented by inheriting classes.
        :param hue: Angle range 0 - 360.

        :return: Returns RGB color for specified angle.
        """
        raise NotImplementedError


class PrimarySineWheel(ColorWheel):
    def getrgb(self, angle):
        """
        Get sine wave RGB color from an angle.

        :param hue: Angle range 0 - 360.

        :return: Returns RGB color for specified angle.
        """
        # force angle into range
        value = angle % 360
        if value < 0:
            value += 360
        scale = 255 / 2

        # get colors based on value, red first
        if value < 120:
            red = round((math.cos(math.radians(value * 1.5)) + 1) * scale)
        elif value >= 240:
            red = round((1 - math.cos(math.radians((value - 240) * 1.5))) * scale)
        else:
            red = 0
        # handle green
        if value < 240:
            green = round((1 - math.cos(math.radians(value * 1.5))) * scale)
        else:
            green = 0
        # handle blue
        if value < 120:
            blue = 0
        else:
            blue = round((1 - math.cos(math.radians((value - 120) * 1.5))) * scale)

        return Color(red, green, blue)


class ColorBlendWheel(ColorWheel):
    """Color Wheel that will blend between colors in a list."""
    def __init__(self, colors):
        # Save list of colors. It is expected that the first and last
        # colors are the same
        self._colors = colors

    def getrgb(self, angle):
        """
        Get a blend RGB color from a set of colors using an angle.

        :param angle: Angle range 0 - 360.

        :return: Returns RGB color for specified angle.
        """
        # if there is only one color then return it
        if len(self._colors) == 1:
            return self._colors[0]

        # force angle into range
        value = angle % 360
        if value < 0:
            value += 360

        # determine section values from number of colors
        sectionDegrees = 360 / (len(self._colors) - 1)
        sectionCurrent = int(value / sectionDegrees)
        sectionValue = value - sectionCurrent * sectionDegrees
        sectionBias = sectionValue / sectionDegrees
        fromColor = self._colors[sectionCurrent]
        toColor = self._colors[sectionCurrent + 1]
        # get RGB color
        color = fromColor.blend(toColor, sectionBias)
        #print("∠=%.2f S∠=%.2f S=%d Bias=%.2f C=(%s)" % (value, sectionValue, sectionCurrent, sectionBias, color))
        return(color)


class PrimaryBlendWheel(ColorBlendWheel):
    """Color Wheel that will blend between primary colors."""
    def __init__(self):
        super().__init__(Color.Primary)


class RainbowBlendWheel(ColorBlendWheel):
    """Color Wheel that will blend between rainbow colors."""
    def __init__(self):
        super().__init__(Color.Rainbow)


class ChristmasBlendWheel(ColorBlendWheel):
    """Color Wheel that will blend between Christmas colors."""
    def __init__(self):
        super().__init__(Color.Christmas)


class HalloweenBlendWheel(ColorBlendWheel):
    """Color Wheel that will blend between Halloween colors."""
    def __init__(self):
        super().__init__(Color.Halloween)


class ColorBounceWheel(ColorWheel):
    """Color Wheel that will beat intensity between colors in a list."""
    def __init__(self, colors):
        # Save list of colors. It is expected that the first and last
        # colors are the same
        self._colors = colors

    def getrgb(self, angle):
        """
        Get a beat RGB color from a set of colors using an angle.

        :param angle: Angle range 0 - 360.

        :return: Returns RGB color for specified angle.
        """
        # force angle into range
        value = angle % 360
        if value < 0:
            value += 360

        # determine section values from number of colors
        sectionDegrees = 360 / (len(self._colors) - 1)
        sectionValue = value + sectionDegrees / 2
        sectionCurrent = int(sectionValue / sectionDegrees)
        color = self._colors[sectionCurrent]
        # get intensity based on angle
        intensity = math.fabs(math.cos(math.radians(value * (len(self._colors) - 1) / 2)))
        # correct color selected now adjust color intensity
        red = color.r * intensity
        green = color.g * intensity
        blue = color.b * intensity
        color = Color(red, green, blue)
        #print("∠=%.2f S∠=%.2f S=%d I=%.2f C=(%s)" % (value, sectionValue, sectionCurrent, intensity, color))
        return(color)


class PrimaryBounceWheel(ColorBounceWheel):
    """Color Wheel that will beat intensity between primary colors."""
    def __init__(self):
        super().__init__(Color.Primary)


class RainbowBounceWheel(ColorBounceWheel):
    """Color Wheel that will beat intensity between rainbow colors."""
    def __init__(self):
        super().__init__(Color.Rainbow)


class ChristmasBounceWheel(ColorBounceWheel):
    """Color Wheel that will beat intensity between Christmas colors."""
    def __init__(self):
        super().__init__(Color.Christmas)


class HalloweenBounceWheel(ColorBounceWheel):
    """Color Wheel that will beat intensity between Halloween colors."""
    def __init__(self):
        super().__init__(Color.Halloween)
