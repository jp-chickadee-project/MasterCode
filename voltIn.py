#!/usr/bin/env python3
# http://raspi.tv/2013/controlled-shutdown-duration-test-of-pi-model-a-with-2-cell-lipo
# DO NOT use this script without a Voltage divider or other means of 
# reducing battery voltage to the ADC.
import time
import os
import sys
import subprocess
import string
import RPi.GPIO as GPIO
from datetime import datetime
from time import gmtime, strftime

GPIO.setmode(GPIO.BCM)


########## Program variables you might want to tweak ###########################
adcs = [0] # 0 which port the voltage divider is connectd to the mpc3002
reps = 10 # how many times to take each measurement for averaging
cutoff = 12 # cutoff voltage for the battery
previous_voltage = cutoff + 1 # initial value
time_between_readings = 10 # seconds between clusters of readings

# Define Pins/Ports
SPICLK = 8
SPIMISO = 22
SPIMOSI = 16
SPICS = 27

#Set up ports
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

################################# CODE #########################################
################################################################################

# read SPI data from MCP3002 chip, 2 possible adc's (0 & 1)
# this uses a bitbang method rather than Pi hardware spi
# modified code based on an adafruit example for mcp3008
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
    if adcnum > 1 or adcnum < 0:
        return -1
    if adcnum == 0:
        commandout = 0x6
    else:
        commandout = 0x7

    GPIO.output(cspin, True)
    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)     # bring CS low
    commandout <<= 5    # we only need to send 3 bits here
    for i in range(3):
        if commandout & 0x80:
            GPIO.output(mosipin, True)
        else:   
            GPIO.output(mosipin, False)
        commandout <<= 1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)

    adcout = 0
    # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 1
        if (GPIO.input(misopin)):
            adcout |= 0x1

    GPIO.output(cspin, True)
    adcout /= 2       # first bit is 'null' so drop it
    return adcout


def getVoltage():
    try:
        for adcnum in adcs:
            adctot = 0
            for i in range(reps):
                read_adc = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                adctot += read_adc
                time.sleep(0.05)
            read_adc = adctot / reps / 1.0

        volts = (1.41 / 93.4) * read_adc + .0195289079
        #GPIO.cleanup()
        return round(volts, 2)
    except:
        #GPIO.cleanup()
        print("Could not get volts")


def getVoltage2():
    try:    
        for adcnum in adcs:
            # read the analog pin
            adctot = 0
            for i in range(reps):
                read_adc = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                adctot += read_adc
                time.sleep(0.05)
            read_adc = adctot / reps / 1.0
            #print (read_adc)
            #print ("location 1")
            
            # convert analog reading to Volts = ADC * ( 3.33 / 1024 )
            # 3.33 tweak according to the 3v3 measurement on the Pi
            #volts = read_adc * ( 3.1 / 1024.0)
            #print(read_adc)
            #print((1.41/93.4) * read_adc + .0195289079)
            #volts = read_adc * ( 3.1 / 1024.0 ) * 5.0470403175
            volts = (1.41 / 93.4) * read_adc + .0195289079
            voltstring = str(volts)[0:5]
            #print ("Battery Voltage: %.2f" % volts)
            # put safeguards in here so that it takes 2 or 3 successive readings
            '''if volts <= cutoff and previous_voltage <= cutoff:
                # initiate shutdown process
                print ("OK. Syncing file system, then we're shutting down.")
                command = os.system("sync")
                if command == 0:
                    command = "/us/bin/sudo /sbin/shutdown now"
                    #process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                    #output = process.communicate()[0]
                    #print output'''
            #previous_voltage = volts
        #time.sleep(time_between_readings)
        return volts
    except:
        print ("Could not get voltage")


def logVoltage(voltage):
    logOut = open("voltageLog.out", "a")
    logOut.write("%s" % (voltage))
    logOut.write(" %s" % (datetime.fromtimestamp(time.time())))
    logOut.write('\n')


def main():
    logVoltage(getVoltage2())
    logVoltage(getVoltage())
    GPIO.cleanup()
    sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nShuting down RFID antenna")
        GPIO.cleanup()
        sys.exit(0)


