import time
import serial
import sys
import json
import requests
import RPi.GPIO as GPIO


SERVER_API = "http://euclid.nmu.edu:18155/api/visits/"
DATA =         #Figure out how to auto-fill 'data' section of post() request. maybe use a method to compile it and once compiled put back into

def main():
    GPIO.setup(23, GPIO.OUT)
    GPIO.output(23, False)
    port_RFID = serial.Serial('/dev/serial0', 9600)

    readCounter = 0
    ID = ""
    prevID = ""
    prevTime = 0

    while True:
        read_byte = port_RFID.read()
        if read_byte == b'\x02':
            for bCounter in range(10):
                read_byte = port_RFID.read()
                ID = ID + read_byte.decode("utf-8")

            timeStamp = int(time.time())
            if ID == prevID and timeStamp - prevTime < 2:
                GPIO.output(23, False)
                time.sleep(.500)
                port_RFID.flushInput()
                ID = ""
                continue
            PrevID = ID
            prevTime = timeStamp

            GPIO.output(23, True)
            readCounter += 1
            print('%d:%s:%a' %(readCounter, ID, timeStamp))

            #Need to automatically pull data from RFID here.. Not use hard coded data.

            post = requests.post(SERVER_API, )