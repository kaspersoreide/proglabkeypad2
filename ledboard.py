import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

class LEDboard:
    def __init__(self):
        self.LEDs = [16, 21, 20]
        self.leds_enabled = [False, False, False,
                             False, False, False]
        for i in range(3):
            GPIO.setup(self.LEDs[i], GPIO.OUT)
    def turn_off_LEDs(self):
        for i in range(3):
            GPIO.setup(self.LEDs[i], GPIO.IN)
            #GPIO.output(self.LEDs[i], GPIO.LOW)
    def flash_LEDs(self):
        self.turn_off_LEDs()
        for i in range(6):
            if not self.leds_enabled[i]:
                continue
            led_index = i // 2
            switch = i % 2
            pin1 = self.LEDs[led_index]
            pin2 = self.LEDs[(led_index + 1) % 3] 
            pin3 = self.LEDs[(led_index + 2) % 3] 
            self.turn_off_LEDs()
            GPIO.setup(pin1, GPIO.OUT)
            GPIO.setup(pin2, GPIO.OUT)
            GPIO.setup(pin3, GPIO.IN)
            if switch == 1:
                GPIO.output(pin1, GPIO.LOW)
                GPIO.output(pin2, GPIO.HIGH)
            else:
                GPIO.output(pin2, GPIO.LOW)
                GPIO.output(pin1, GPIO.HIGH)
        self.turn_off_LEDs()

    def enable_LEDs(self):
        for i in range(6):
            self.leds_enabled[i] = True
    def disable_LEDs(self):
        for i in range(6):
            self.leds_enabled[i] = False
    def lid_ldur(self, index, duration):
        self.disable_LEDs()
        self.leds_enabled[index] = True
        t = time.time()
        while time.time() - t < duration:
            self.flash_LEDs()
        self.disable_LEDs()

    def test_leds(self):
        pin1 = 21
        pin2 = 16
        pin3 = 20
        GPIO.setup(pin1, GPIO.IN)
        GPIO.setup(pin2, GPIO.OUT)
        GPIO.setup(pin3, GPIO.OUT)
        GPIO.output(pin3, GPIO.HIGH)
        for i in range(6):
            led_index = i // 2
            switch = i % 2
            pin1 = self.LEDs[led_index]
            pin2 = self.LEDs[(led_index + 1) % 3] 
            pin3 = self.LEDs[(led_index + 2) % 3] 
            print(str(led_index), str(switch), str(pin1), str(pin2), str(pin3))


    def power_up(self):
        self.disable_LEDs()
        for i in range(6):
            t = time.time()
            self.leds_enabled[i] = True
            while time.time() - t < 0.7:
                self.flash_LEDs()
        self.disable_LEDs()

    def power_down(self):
        self.enable_LEDs()
        for i in range(6):
            t = time.time()
            while time.time() - t < 0.7:
                self.flash_LEDs()
            self.leds_enabled[i] = False 
        self.disable_LEDs()

    def wrong(self):
        self.disable_LEDs()
        for i in range(3):
            t = time.time()
            for j in range(6):
                self.leds_enabled[j] = not self.leds_enabled[j]
            while time.time() - t < 0.4:
                self.flash_LEDs()
        self.disable_LEDs()

    def correct(self):
        self.disable_LEDs()
        for i in range(3):
	        self.leds_enabled[2 * i] = True
	        self.leds_enabled[2 * i + 1] = True
                t = time.time()
                while time.time() - t < 0.9:
                    self.flash_LEDs()
	        self.leds_enabled[2 * i] = False
	        self.leds_enabled[2 * i + 1] = False

