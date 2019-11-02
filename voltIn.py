#!/usr/bin/env python3
"""Bitbangs signals from MCP3002 ADC and converts into a human readable voltage.

voltageDivider: Which port the voltage divider is attached to the ADC(Either 0 or 1).
reps: How many samples to take for averaging voltage.
SPICLK: SPI clock
SPIMISO: SPI Master In, Slave Out - Master receiving data, slave sending out data
SPIMOSI: SPI Master Out, Slave In - Master sending out data, slave receiving data
SPICS: Slave wake up pin, Low = on
getVoltage() is the method you want to call.
"""
import time
import os
import sys
import RPi.GPIO as GPIO
from datetime import datetime
from time import gmtime, strftime

voltageDividerPort = [0]
reps = 10
SPICLK = 8
SPIMISO = 22
SPIMOSI = 16
SPICS = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)


def cycleClock(clockPin):
    """Cycles the SPICLK."""
    GPIO.output(clockPin, GPIO.HIGH)
    GPIO.output(clockPin, GPIO.LOW)


def readADC(adcPort, clockPin, mosiPin, misoPin, csPin):
    """Bitbangs signals from the ADC.
    
    Refer to the MCP3002 datasheet, pages 13 and 14.
    Sends the ADC two signals via MOSI, then opens up MISO for
    communications. Data is sent on the falling edge
    of the clock via the MISO pin. Master recieves
    one empty bit, one NULL bit, then 10 data bits.
    Put ADC to sleep then lop off the NULL bit and return.
    """
    GPIO.output(csPin, GPIO.HIGH)
    GPIO.output(clockPin, GPIO.LOW)
    GPIO.output(csPin, GPIO.LOW)

    GPIO.output(mosiPin, GPIO.HIGH)
    for cycles in range(3):
        cycleClock(clockPin)
        if cycles is 1:
            GPIO.output(mosiPin, GPIO.LOW)

    adcDataBits = 0
    # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
        cycleClock(clockPin)
        adcDataBits <<= 1
        if (GPIO.input(misoPin)):
            adcDataBits |= 0x1

    GPIO.output(csPin, GPIO.HIGH)
    adcDataBits /= 2
    return adcDataBits


def getVoltage():
    """Gets the raw data from readadc then converts into volts and returns it.

    [(1.41 / 93.4) * read_adc + .0195289079] was calculated using raw
    values from readADC() and using a multimeter on the battery. 
    y = mx + b where y is the volts.
    """
    try:
        for adcPort in voltageDividerPort:
            adcTotal = 0
            for i in range(reps):
                read_adc = readADC(adcPort, SPICLK, SPIMOSI, SPIMISO, SPICS)
                adcTotal += read_adc
                time.sleep(0.05)
            read_adc = adcTotal / reps / 1.0

        volts = (1.41 / 93.4) * read_adc + .0195289079
        return round(volts, 2)
    except:
        return -1


def logVoltage(voltage):
    """Logs the voltage in cwd/voltageLog.out."""
    logOut = open("voltageLog.out", "a")
    logOut.write("%s" % (voltage))
    logOut.write(" %s" % (datetime.fromtimestamp(time.time())))
    logOut.write('\n')


def main():
    logVoltage(getVoltage())
    read_adc = readADC(0, SPICLK, SPIMOSI, SPIMISO, SPICS)
    print(read_adc)
    GPIO.cleanup()
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        sys.exit(0)


