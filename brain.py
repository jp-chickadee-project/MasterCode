#!/usr/bin/env python3
"""Main program of the JP Chickadee Project Feeder rig V2.

PortRF = serial port for the RFID reader
logFilePath
backup2Directory
transmit2Directory
dupeCheckInterval = threshold at which duplicate reads are counted against
voltageCheckInterval = interval at which voltages are checked
counterThreshold = how many reads until a logfile is closed, backed up, and replaced
# using sendData().
voltageThreshold = threshold at which the battery voltage is check against. If below, shutdown system
This program acts as the "brains" of the feeder V2. Logging RFIDs and periodically checking voltages.
TODO: Interface with battery Mech, LTE conversion mode
github: https://github.com/jp-chickadee-project
"""
import time
import serial
import sys
import subprocess
import json
import requests
import shutil
import os
import RPi.GPIO as GPIO
import re
import voltIn
from datetime import datetime
from hx711 import HX711

PortRF = serial.Serial('/dev/serial0', 9600, timeout = 5)
logFilePath = "/home/pi/MasterCode/log0.out"
backup2Directory = "/home/pi/MasterCode/backup/"
transmit2Directory = "/home/pi/MasterCode/transmit/"
dupeCheckInterval = 500000000 # .5 seconds 
voltageCheckInterval = 600 # 600 seconds
counterThreshold = 100
voltageThreshold = 10.6

def cleanAndExit():
    "Closes serial ports and cleans up the GPIO pins."
    PortRF.close()
    GPIO.cleanup()
    sys.exit()


def sendData():
    """Starts transmit.out via subprocess to send completed logfiles."""
    print("** starting send.. **")
    subprocess.Popen(["/home/pi/lmic-rpi-lora-gps-hat/examples/transmit/build/transmit.out"], stdout=subprocess.DEVNULL)
    print("** transmit.out started **")


# Enable the RFID tag and associating GPIO pins
def rfidSensorSetup():
    """Set GPIO to BCM mode and sets up BCM pin 12 for LED."""
    print("setting up RFID...\n")
    GPIO.setmode(GPIO.BCM) #will need this for implementing LEDs
    GPIO.setup(12, GPIO.OUT)
    GPIO.output(12, False)
    

def getOnFile():
    """Checks if 'on.txt' is present within cwd, returns true if it is."""
    for file in os.listdir("/home/pi/MasterCode/"):
        if file.endswith("on.txt"):
            print("Found on.txt. Not calling c-code transmit.")
            return True


def getTranLogFile(): # Gets most recent log.out file.
    """Finds the highest # in cwd/transmit/log#.out and returns it."""
    tmp = 0
    for file in os.listdir("/home/pi/MasterCode/transmit/"):
        for char in file:
            if char.isdigit() and int(char) > int(tmp):
                tmp = char
            else:
                continue
    return tmp


def fetchData():
    """Fetches the input buffer of /dev/serial0(PortRF) and sends it to logStuff with a timestamp, checking voltage every voltageCheckInterval seconds.
    
    prevVoltageTime = last time voltage was checked
    readCounter = how many reads we have on current logOutput
    ID = current working RFID
    prevID = previous RFID
    prevTime = previous RFID timestamp
    logFileCount = how many logfiles we have during this session
    logOutput = FD of current working log0.out
    While PortRF is still open, continuelly check for the valid start bit("x02"). Then read in the next 10 bits
    and decode them into a string, incrementing readCounter. Must reset ID after every iteration or else decode
    will be trashed. After every counterThreshold reads, logOutput is closed, backed up, and moved to cwd/transmit.
    """
    print("fetching data from RFID antenna\n")
    prevVoltageTime = time.time()
    readCounter = 0
    ID = ""
    prevID = ""
    prevTime = 0
    logFileCount = 0
    logOutput = open("log0.out", "a")

    while PortRF.is_open:
        currentVoltageTime = time.time()
        if(currentVoltageTime - prevVoltageTime > voltageCheckInterval):
            voltageCheck()
            prevVoltageTime = voltageTime

        if readCounter < counterThreshold:
            print("waiting for read")
            read_byte = PortRF.read()
            if read_byte:
                if read_byte==b'\x02':
                    for bCounter in range(10):
                        print(read_byte)
                        read_byte=PortRF.read()
                        ID = ID + read_byte.decode('utf-8')
                
                    timeStamp = (time.time_ns())
                    if ID == prevID and timeStamp - prevTime < dupeCheckInterval:
                        PortRF.reset_input_buffer()
                        ID = ""
                        continue

                    prevID = ID
                    prevTime = timeStamp
                    GPIO.output(12, True)
                    readCounter += 1
                    logOutput.write('%s''%s' % (ID,prevTime / 1000000000) + '\n')
                    print ('%d:%s' % (readCounter, ID))     # These prints are for testing
                    print("prevTime: ", prevTime)           # Same here.
                    ID = ""
                    print("//////////////////////////////")
                    GPIO.output(12, False)
                    PortRF.reset_input_buffer()
                    
                
            time.sleep(.05)
        else:
            logFileCount += 1
            logOutput.close()
            logStuff()
            print("logFileCount: ",logFileCount)
            if not getOnFile():
                sendData()
            
            logOutput = open("log0.out", "a")    #will overwrite the current log.out file if one exists, or create one if DNE
            readCounter = 0


def replacer(s, newstring, index, nofail=False):
    """Insert the new string between "slices" of the original, then return the new string."""
    return s[:index] + newstring + s[index + 1:]


def logStuff():
    """docstring placeholder"""
    tmpString = "log0.out"
    tmp = ""
    if int(getTranLogFile()) >= 0:
        newestLogNum = getTranLogFile()
        newestLogNum = int(newestLogNum) + 1
        tmp = replacer(tmpString, str(newestLogNum), 3) # new file name to save as into /backup and /transmit
        backupLog = backup2Directory + datetime.now().strftime("%Y-%m-%d@%H:%M:%S") + '.out'
        transmitLog = transmit2Directory + tmp
        print("newTmp: ", tmp)
        shutil.copy(logFilePath,backupLog)
        shutil.copy(logFilePath,transmitLog)
        if os.path.exists("/home/pi/MasterCode/log0.out"):
            os.remove(logFilePath)

        print("tmp: ", tmp)
    else:
        print("No log files found in transmit Directory")
        shutil.copy(logFilePath, backup2Directory)
        shutil.copy(logFilePath, transmit2Directory)
        if os.path.exists("/home/pi/MasterCode/log0.out"):
            os.remove(logFilePath)
    

def voltageCheck():
    """Checks the voltage using voltIn.getVoltage, shutdown the system if voltage is below voltageThreshold."""
    voltage = voltIn.getVoltage()

    if voltage <= voltageThreshold:
        GPIO.cleanup()
        subprocess.call(["shutdown"])


def main():
    print("Here is Main routine")
    rfidSensorSetup()
    voltageCheck()
    fetchData()
    cleanAndExit()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        cleanAndExit()

