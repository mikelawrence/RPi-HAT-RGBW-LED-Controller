# RGBW LED Controller HAT Test Software
The test software is written in Python 3 and suppors all hardware elements on the RGBW LED Controller HAT.

The PCA9685 driver is based on Adafruit's Python PCA9685 library (PCA9685.py). While this library works it had some problems. First every register write is a single 8-bit I<sup>2</sup>C transaction even those registers like LEDn_ON which are actually two 8-bit registers together. So I changed all multi-register writes to support the writeList function which writes multiple bytes from a starting address in a single transaction. This required also setting the AI bit in the MODE1 register. This configures the PCA9685 to auto-increment the address counter. Finally I added a function that writes the LED On and LED Off values for multiple PWM channels starting with CH0. This allows the RGB PWM values to be updated simultaneously.

The rgbled.py file provides most of the color processing and RGB LED control through the PCA9685 PWM controller. Color is defined as a tuple representing a color using Red, Green, and Blue values with a range of [0:255]. The LinearWheel and SineWheel classes provide a convenient HSV to RGB color converter that takes a Hue angle with the range [0:360] and converts it to a color. The Linear Wheel uses a linear translation of colors while the SineWheel uses a Sine wave translation of colors. This [website](http://www.instructables.com/id/How-to-Make-Proper-Rainbow-and-Random-Colors-With-/) has a good explanation of the difference between linear and sinusoid hue translations.

The RgbLed class accepts RGB colors and sets the PCA9685 to produce that color. This class also provides gamma correction if requested.

## Example
Running test.py will start rotating through the colors of the rainbow and periodically checking the CPU and HAT temperatures.

```
pi@rpi-rgb-led-1:~/projects/RPi-HAT-RGBW-LED-Controller/code $ ./test.py
RPi RGBW LED Controller HAT Test
Found 1-Wire temp sensor 00000991f822

Press any key to exit.
CPU Temp = 47.2C, HAT Temp 35.4C
CPU Temp = 47.2C, HAT Temp 35.6C
CPU Temp = 47.2C, HAT Temp 35.7C
CPU Temp = 47.2C, HAT Temp 35.8C
CPU Temp = 47.8C, HAT Temp 35.9C
```

# Acknowledgments
The following python libraries were used to demonstrate the functionality of the Raspberry Pi RGBW LED Controller HAT.
* [Python3 w1thermsensor](https://github.com/timofurrer/w1thermsensor)
* [Adafruit Python GPIO](https://github.com/adafruit/Adafruit_Python_GPIO)
The following libraries were used but had to be modified.
* [Adafruit Python PCA9685](https://github.com/adafruit/Adafruit_Python_PCA9685).
The following code was pulled from the Internet
* [kbhit.py](http://home.wlu.edu/~levys/software/kbhit.py) from Simon D. Levy
* [timer.py](https://stackoverflow.com/questions/12435211/python-threading-timer-repeat-function-every-n-seconds)
