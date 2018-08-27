import time
import serial
import sys
import json
import requests
import RPi.GPIO as GPIO

import RFIDreaderbackup   #File for RFIDreader.py
import LTE_test           #File to boot LTE CPE when Pi is started.


def main():

    LTE_TEST = pathroot + '/MasterCode/LTE_test.py'    #Will need to be directory on Pi of where file is located
    execfile(LTE_TEST)      #Run LTE_test.py from directory

    execfile(RFIDreaderbackup)

    #Load cell activates RFIDreader.py code.
        #(inside RFIDreader.py, save information to a file.)
    




if __name__ == '__main__':
    try:
        main()



    except KeyboardInterrupt:
        print("Shuting down")
        GPIO.cleanup() #Will need this when we implement LEDs
        sys.exit(0)
