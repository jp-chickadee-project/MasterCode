import time, serial, sys, json, requests
import RPi.GPIO as GPIO


# Do these need to be in Main? Do not think so... These should set up the pin(s) for communicating data
GPIO.setup(23, GPIO.OUT)
GPIO.output(23, False)
port_RFID = serial.Serial('/dev/serial0', 9600) #this will either stay here or relocate inside compielRFID method.
STARTBIT_RFID = '\x02' #hard coded rfid tag beginning.. Cannot have this for final


SERVER_API = "http://euclid.nmu.edu:18155/api/visits/"
DATA =         #Figure out how to auto-fill 'data' section of post() request. maybe use a method to compile it and once compiled put back into


def compileRFID(ID, feederID, visitTimestamp, temp, mass, bandCombo):
    #figure out how the data is coming in from the RFID reader.. Parse the data
    #Hopeufully data will be 'grouped'. set groups to specified vars.

    data_RFID = serial.Serial('/dev/serial0', 9600)
    data_RFID = str(data_RFID.strip(startBit_RFID)) #strip off starting '\x02', leaving only the tag number
    

def main():


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