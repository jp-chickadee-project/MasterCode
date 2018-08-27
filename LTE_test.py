import time
import sys
import RPi.GPIO as GPIO


    #Send signal to LTE puck in order to turn on. Should automatically connect to LTE
def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(24, GPIO.OUT)
    GPIO.output(24, True)
    time.sleep(3)
    GPIO.output(24, False)
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Shutting Down")
        GPIO.output(24, False)
        GPIO.cleanup()
        sys.exit(0)
