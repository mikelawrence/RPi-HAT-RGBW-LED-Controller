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
from collections import namedtuple

"""RGB color tuple."""
class Color(namedtuple('Color', 'r g b')):

    def blend(self, other, bias):
        """
        Return a new color, interpolated between this color and other color by
        an amount specified by blend, which ranges from 0.0 (entirely
        this color) to 1.0 (entirely other color).
        :param other: The other color interpolate between.
        :param bias: The blend between colors range 0.0 - 1.0
        """
        if bias > 1.0:
            tobias = 1.0
        else:
            tobias = bias
        frombias = 1.0 - tobias
        red = self.r * frombias + other.r * tobias
        green = self.g * frombias + other.g * tobias
        blue = self.b * frombias + other.b * tobias
        return Color(red, green, blue)

    def gamma(self, gamma=2.8, max=255):
        """
        Return a list color values which is a gamma corrected version of
        this color.

        :param color: The color to perform the gamma correction on.
        :param gamma: The gamma value.
        :param max: Specifies full scale output of the gamma correction.

        :return: List of RGB values gamma corrected and scaled.
        """
        return [round(max * ((c / 255) ** gamma)) for c in self]

    def __str__(self):
        return "%d, %d, %d" % (self.r, self.g, self.b)

    def __repr__(self):
        return "Color(r=%d, g=%d, b=%d)" % (self.r, self.g, self.b)

Color.Rainbow = [Color(255,   0,   0), # Red
                 Color(171,  85,   0), # Orange
                 Color(171, 171,   0), # Yellow
                 Color(  0, 255,   0), # Green
                 Color(  0, 171,  85), # Aqua
                 Color(  0,   0, 255), # Blue
                 Color( 85,   0, 171), # Purple
                 Color(148,   0, 211), # Violet
                 Color(255,   0,   0)] # and back to Red

Color.Primary = [Color(255,   0,   0), # Red
                 Color(255, 255,   0), # Yellow
                 Color(  0, 255,   0), # Green
                 Color(  0, 255, 255), # Cyan
                 Color(  0,   0, 255), # Blue
                 Color(255,   0, 255), # Purple
                 Color(255,   0,   0)] # and back to Red

Color.Halloween = [Color(255,   0,   0), # Red
#                   Color(255, 100,   0), # Orange
#                   Color( 85,   0, 171), # Purple
                   Color(127,   0, 255), # Purple
                   Color(255,   0,   0)] # Red

Color.Christmas = [Color(255,   0,   0), # Red
#                   Color(255, 215,   0), # Gold
                   Color(  0, 255,   0), # Green
                   Color(255,   0,   0)] # Red



Color.Red       = Color(255, 0 , 0)
Color.Orange    = Color(255, 127, 0)
Color.Yellow    = Color(255, 255, 0)
Color.Green     = Color(0, 255, 0)
Color.Blue      = Color(0, 0, 255)
Color.Indigo    = Color(75, 0, 130)
Color.Violet    = Color(148, 0, 211)
