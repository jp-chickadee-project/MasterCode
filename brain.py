import time
import serial
import sys
import subprocess
import json
import requests
import shutil
import os
import RPi.GPIO as GPIO
from hx711 import HX711
#import mastaCode
#import RFID

# change log.out. Will only need the filepath, not a hardcoded .out file.
PortRF = serial.Serial('/dev/serial0',9600)     # /dev/serial0 is the RFID setup..
backupDirectory = "/home/pi/MasterCode/backup/log.out"
transmitDirectory = "/home/pi/MasterCode/transmit/log.out"
logFilePath = "/home/pi/MasterCode/log.out"


def cleanAndExit():
    print("Cleaning...")
    GPIO.cleanup
    sys.exit()


def sendData():
    print("** starting send.. **")
    subprocess.Popen(["/home/pi/lmic-rpi-lora-gps-hat/examples/transmit/build/transmit.out"], stdout=subprocess.DEVNULL)
    #subprocess.Popen(["/home/pi/lmic-rpi-lora-gps-hat/examples/transmit/build/transmit.out"])
    print("** transmit.out started **")


# Enable the RFID tag and associating GPIO pins
def rfidSensorSetup():
    print("setting up RFID...\n")
    GPIO.setmode(GPIO.BCM) #will need this for implementing LEDs
    GPIO.setup(12, GPIO.OUT)
    GPIO.output(12, False)
    

def sendLogRFID():
    print("sending RFID Log information")


# Enable the LoadCell... Not using for now *****
def loadcellSetup():
    print("setting up LoadCell")

def getOnFile(): # Possibly return True here??
    for file in os.listdir("/home/pi/MasterCode/"):
        if file.endswith(".txt"):
            print("Found on.txt")
            return True

def getTranLogFile():
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
    
    PortRF = serial.Serial('/dev/serial0',9600)     # /dev/serial0 is the ..... Find out.
    readCounter = 0
    ID = ""
    prevID = ""
    prevTime = 0
    logFileCount = 0

    while True:
        if readCounter < 3:
            read_byte = PortRF.read()
            if read_byte==b'\x02':
                for bCounter in range(10):
                    read_byte=PortRF.read()
                    ID = ID + read_byte.decode("utf-8")
                
                timeStamp = (int)(time.time())
                if ID == prevID and timeStamp - prevTime < 2:
                    GPIO.output(12, False)
                    time.sleep(.500)
                    PortRF.flushInput()
                    ID = ""
                    continue
                prevID = ID
                prevTime = timeStamp

                GPIO.output(12, True)
                readCounter += 1
                #print ('%d:%s:%a' %(readCounter, ID, timeStamp))
                logOutput = open("log.out", "a")   # This is the log file that will store the RFID 'ID' and a timestamp associated with it.
                logOutput.write('%s''%s' % (ID,prevTime) + '\n')
                #logOutput.write(' time: %d' % (prevTime) + '\n')
                print ('%d:%s' % (readCounter, ID))     # These prints are for testing
                print("prevTime: ", prevTime)           # Same here.
                """r = requests.post("http://euclid.nmu.edu:18155/api/visits/", 
                    data = {
                        "rfid": ID,
                        "feederID": "CLIF",
                        "visitTimestamp": int(time.time()),
                        "temperature": 0,
                        "mass": 108,
                        "bandCombo":"#a0/V"
                    }
                )
                print("status code:" + str(r.status_code))
                print(r.text)"""
                ID = ""
                print("//////////////////////////////")
                logOutput.close()       # close file just before sleep. Should allow enough time to reopen.. (idk if thats a thing)
                time.sleep(.50)
                GPIO.output(12, False)
                PortRF.flushInput()
        else:
            logFileCount += 1
            logOutput.close()
            logStuff()
            if getOnFile():
                break
            else:
                print("logFileCount: ",logFileCount)
                sendData()
                logOutput = open("log.out", "a")    #will overwrite the current log.out file if one exists, or create one if DNE
                readCounter = 0



def logStuff():
    shutil.copyfile(logFilePath, backupDirectory) #new
    shutil.copyfile(logFilePath, transmitDirectory)   #ne
    if os.path.exists("/home/pi/MasterCode/log.out"):   #new
        os.remove(logFilePath)  #new


def scan(logOutput):
    hx = HX711(5, 6)
    hx.set_reading_format("LSB", "MSB")
    hx.set_reference_unit(592)
    hx.reset()
    hx.tare()
   
    readCounter = 0
    ID = ""
    prevID = ""
    prevTime = 0

    while True:
        if readCounter < 3:
            print("////////////////////////////////////////////////")
            val = hx.get_weight(1) #uncomment
            val2 = hx.get_weight(1) #uncomment
            if val2 < val: #uncomment
                val = val2 #uncomment
            #val = 60
            #if hx.get_weight(5) > 50:
            if val > 50 or val < -50:
                read_byte = PortRF.read()
                if read_byte:
                    if read_byte==b'\x02':
                        for bCounter in range(10):
                            read_byte=PortRF.read()
                            ID = ID + read_byte.decode("utf-8")
                else:
                    ID = "1111111111"

                timeStamp = (int)(time.time())
                if ID == prevID and timeStamp - prevTime < 1:
                    #GPIO.output(23, False)
                    #time.sleep(.500)
                    PortRF.flushInput()
                    ID = ""

                else:
                    readCounter+=1
                    prevID = ID
                    prevTime = timeStamp
                    logOutput.write('%s' % (ID) + '\n')


            print ('%d:%s' % (readCounter, ID))     # These prints are for testing
            print("timestamp: ", prevTime)
            print(val)
            ID = ""
            PortRF.flushInput()
            hx.power_down()
            time.sleep(.4)
            hx.power_up()
        else:
            logOutput.close()
            logStuff()
            sendData()
            #sendData() #remove this line after testing above if: statement
            logOutput = open("log.out", "a")#will overwrite the current log.out file if one exists, or create one if DNE
            readCounter = 0


def main():
    print("Here is Main routine")
    #sendData()
    
    logOutput = open("log.out", "a")   # This is the log file that will store the RFID 'ID' and a timestamp associated with it.
    #scan(logOutput) 
    rfidSensorSetup()
    fetchData()
    logStuff()  #breaking here because logfile DNE after one complete cycle...*********

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nShuting down RFID antenna")
        
        GPIO.cleanup() #Will need this when we implement LEDs
        sys.exit(0)
