import time
import serial
import sys
import json
import requests
import RPi.GPIO as GPIO


def main():
    GPIO.setmode(GPIO.BCM) #will need this for implementing LEDs
    GPIO.setup(23, GPIO.OUT)
    GPIO.output(23, False)
    PortRF = serial.Serial('/dev/serial0',9600)
    
    readCounter = 0
    ID = ""
    prevID = ""
    prevTime = 0
    while True:
        read_byte = PortRF.read()
        if read_byte==b'\x02':
            for bCounter in range(10):
                read_byte=PortRF.read()
                #print('%d:%s' %(bCounter, read_byte))
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
            print ('%d:%s:%a' %(readCounter, ID, timeStamp))
            r = requests.post("http://euclid.nmu.edu:18155/api/visits/", 
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
            print(r.text)
            ID = ""
            print("//////////////////////////////")
            time.sleep(.500)
            GPIO.output(23, False)
            PortRF.flushInput()
    GPIO.cleanup() #exiting the program... Should never get here

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Shuting down")
        GPIO.cleanup() #Will need this when we implement LEDs
sys.exit(0)
