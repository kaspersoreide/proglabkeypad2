import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
import time

class Keypad:
    def __init__(self):
        #index mapped to GPIO-pins
        self.rows = [18, 23, 24, 25]
        self.cols = [17, 27, 22]
        self.signals = [['1', '2', '3'],
                        ['4', '5', '6'],
                        ['7', '8', '9'],
                        ['*', '0', '#']]
        self.last_debounce = time.time()
        for r in self.rows:
            GPIO.setup(r, GPIO.OUT)
        for c in self.cols:
            GPIO.setup(c, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    def poll_buttons(self):
        for i in range(len(self.rows)):
            GPIO.output(self.rows[i], GPIO.HIGH)
            for j in range(len(self.cols)):
                #sleep(0.05)
                if GPIO.input(self.cols[j]) == GPIO.HIGH:
                    if time.time() - self.last_debounce > 0.3:
                        self.last_debounce = time.time()
                        GPIO.output(self.rows[i], GPIO.LOW)
                        return self.signals[i][j]
            GPIO.output(self.rows[i], GPIO.LOW)
    def test():
        GPIO.setup(21, GPIO.OUT)
        GPIO.output(21, GPIO.HIGH)
