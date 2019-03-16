import time
import serial
import sys
import subprocess
import json
import requests
import RPi.GPIO as GPIO
from hx711 import HX711
#import mastaCode
#import RFID



def cleanAndExit():
    print("Cleaning...")
    GPIO.cleanup
    sys.exit()


def sendData():
    subprocess.run(["./home/pi/lmic-rpi-lora-gps-hat/examples/transmit/build/transmit.out"])


# Enable the RFID tag and associating GPIO pins
def rfidSensorSetup():
    print("setting up RFID...\n")
    GPIO.setmode(GPIO.BCM) #will need this for implementing LEDs
    GPIO.setup(23, GPIO.OUT)
    GPIO.output(23, False)
    

def sendLogRFID():
    print("sending RFID Log information")


# Enable the LoadCell... Not using for now *****
def loadcellSetup():
    print("setting up LoadCell")


# Fetch the data from the load cell and RFID reader. Save to 'log.out'. This should allways be running.
# Not necessarily sending to the API but saving to the 'log.out' file to send during specific upLink times.
def fetchData():
    print("fetching data from RFID antenna\n")
    
    PortRF = serial.Serial('/dev/serial0',9600)     # /dev/serial0 is the ..... Find out.
    readCounter = 0
    ID = ""
    prevID = ""
    prevTime = 0
    while True:
        read_byte = PortRF.read()
        if read_byte==b'\x02':
            for bCounter in range(10):
                read_byte=PortRF.read()
                ID = ID + read_byte.decode("utf-8")
                
            timeStamp = (int)(time.time())
            if ID == prevID and timeStamp - prevTime < 2:
                GPIO.output(23, False)
                time.sleep(.500)
                PortRF.flushInput()
                ID = ""
                continue
            prevID = ID
            prevTime = timeStamp

            GPIO.output(23, True)
            readCounter += 1
            #print ('%d:%s:%a' %(readCounter, ID, timeStamp))
            logOutput = open("log.out", "a")   # This is the log file that will store the RFID 'ID' and a timestamp associated with it.
            logOutput.write('%s' % (ID) + '\n')
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
            GPIO.output(23, False)
            PortRF.flushInput()


def scan():
    hx = HX711(5, 6)
    hx.set_reading_format("LSB", "MSB")
    hx.set_reference_unit(592)
    hx.reset()
    hx.tare()

    while True:
        val = hx.get_weight(5)
        print(val)
        hx.power_down() 
        hx.power_up()
        time.sleep(0.5)


def main():
    print("Here is Main routine")
    scan()
    while(True):
        rfidSensorSetup()
        fetchData()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nShuting down RFID antenna")
        GPIO.cleanup() #Will need this when we implement LEDs
        sys.exit(0)
