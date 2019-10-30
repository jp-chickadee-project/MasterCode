#!/usr/bin/env python3
"""docstring placeholder

stuff to say
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
from hx711 import HX711



### Globals ###
PortRF = serial.Serial('/dev/serial0', 9600, timeout = 5)
logFilePath = "/home/pi/MasterCode/log0.out"
backup2Directory = "/home/pi/MasterCode/backup/"
transmit2Directory = "/home/pi/MasterCode/transmit/"
dupeThreshold = 500000000
### End Globals ###

def cleanAndExit():
    PortRF.close()
    GPIO.cleanup()
    sys.exit()


def sendData():
    print("** starting send.. **")
    subprocess.Popen(["/home/pi/lmic-rpi-lora-gps-hat/examples/transmit/build/transmit.out"], stdout=subprocess.DEVNULL)
    print("** transmit.out started **")


# Enable the RFID tag and associating GPIO pins
def rfidSensorSetup():
    print("setting up RFID...\n")
    GPIO.setmode(GPIO.BCM) #will need this for implementing LEDs
    GPIO.setup(12, GPIO.OUT)
    GPIO.output(12, False)
    

def getOnFile():
    for file in os.listdir("/home/pi/MasterCode/"):
        if file.endswith(".txt"):
            print("Found on.txt. Not calling c-code transmit.")
            return True


def getTranLogFile(): # Gets most recent log.out file.
    tmp = 0
    for file in os.listdir("/home/pi/MasterCode/transmit/"):
        for char in file:
            if char.isdigit() and int(char) > int(tmp):
                tmp = char
            else:
                continue
    return tmp
            # print(os.path.join("/home/pi/MasterCode/",file))


# Fetch the data from the load cell and RFID reader. Save to 'log.out'. This should allways be running.
# Not necessarily sending to the API but saving to the 'log.out' file to send during specific upLink times
# using sendData().
def fetchData():
    print("fetching data from RFID antenna\n")
    readCounter = 0
    ID = ""
    prevID = ""
    prevTime = 0
    logFileCount = 0
    logOutput = open("log0.out", "a")

    while PortRF.is_open:
        if readCounter < 100:
            print("waiting for read")
            read_byte = PortRF.read()
            if read_byte:
                if read_byte==b'\x02':
                    for bCounter in range(10):
                        print(read_byte)
                        read_byte=PortRF.read()
                        ID = ID + read_byte.decode('utf-8')
                
                    timeStamp = (time.time_ns())
                    if ID == prevID and timeStamp - prevTime < dupeThreshold:
                        PortRF.flushInput()
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
    # insert the new string between "slices" of the original
    return s[:index] + newstring + s[index + 1:]


def logStuff():
    tmpString = "log0.out"
    tmp = ""
    if int(getTranLogFile()) >= 0:
        newestLogNum = getTranLogFile()
        newestLogNum = int(newestLogNum) + 1
        tmp = replacer(tmpString, str(newestLogNum), 3) # new file name to save as into /backup and /transmit
        backupLog = backup2Directory + tmp
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
    print("Voltage test")
    voltage = voltIn.getVoltage()
    print(voltage)

    if voltage <= 11:
        #GPIO.cleanup()
        #os.system("shutdown now")
        print("SHUTDOWN")


def main():
    print("Here is Main routine")
    rfidSensorSetup()
    voltageCheck()
    fetchData()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        cleanAndExit()


