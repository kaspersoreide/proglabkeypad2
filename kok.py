"""Module for the classes controlling the physical interfaces; Keypad and Led Board"""
import math
import time
import RPi.GPIO as GPIO
from enum import Enum


class Signal:
    @staticmethod
    def digit(signal):
        return ord("0") <= ord(signal) <= ord("9")

    @staticmethod
    def any(signal):
        return True

    @staticmethod
    def asterisk(signal):
        return signal == "*"

    @staticmethod
    def hash(signal):
        return signal == "#"

    @staticmethod
    def led(signal):
        return ord("0") <= ord(signal) <= ord("5")

    @staticmethod
    def yes(signal):
        return signal == "Y"


class State(Enum):
    init = 0
    read1 = 1
    verify = 2
    active = 3
    read2 = 4
    led = 5
    time = 6
    logout = 7
    done = 8


class Rule:
    def __init__(self, source_state, destination_state, signal, action):
        self.source_state = source_state
        self.destination_state = destination_state
        self.signal = signal
        self.action = action

    def match(self, state, signal):
        return self.source_state == state and self.signal(signal)

    def __str__(self):
        return str(self.source_state) + " " + str(self.destination_state) + " " + str(self.signal) + " " + str(self.action)


class FSM:
    def __init__(self, agent):
        self.agent = agent
        self.state = State.init
        self.signal = None
        self.rules = []

    def add_rule(self, new_rule):
        self.rules.append(new_rule)

    def main_loop(self):
        while self.state != State.done:
            self.signal = self.agent.get_next_signal()
            print("signal:", self.signal)
            for rule in self.rules:
                if rule.match(self.state, self.signal):
                    print(rule)
                    self.state = rule.destination_state
                    rule.action(self.agent, self.signal)
                    break
        GPIO.cleanup()
        exit()


class Keypad:
    """Controls the setup and pooling of the physical Keypad"""

    def __init__(self):
        """Defines the keys dictionary"""
        self.__keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]

        self.__row_pins = {
            0: 18,
            1: 23,
            2: 24,
            3: 12
        }

        self.__column_pins = {
            0: 17,
            1: 27,
            2: 22
        }

        self.setup()

    def setup(self):
        """Setup the Raspberry Pi's GPIO mode, and configure its pins"""
        GPIO.setmode(GPIO.BCM)

        # For every row pin, rp
        for row_pin in range(4):
            GPIO.setup(self.__row_pins[row_pin], GPIO.OUT)

        # For every column pin, cp
        for column_pin in range(3):
            GPIO.setup(self.__column_pins[column_pin], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def do_polling(self):
        """Pools the Keypad for the next signal, takes 200 ms if signal found"""
        # The default key_pressed is None in case no key_pressed is found
        key_pressed = None

        # Loop through the rows
        for row_pin in range(4):
            # Power on the row_pin
            GPIO.output(self.__row_pins[row_pin], GPIO.HIGH)

            # Loop through the columns and check for HIGH input
            for column_pin in range(3):
                # Default pressed, set to False if proven LOW
                pressed = True

                # Loop through 20 times, and makes sure that the input is HIGH every time
                # This is a measure-wait-measure loop
                for _ in range(20):
                    # If the input is not HIGH, set pressed to False and break
                    if not GPIO.input(self.__column_pins[column_pin]) == GPIO.HIGH:
                        pressed = False
                        break

                    # Sleep
                    time.sleep(5/1000)

                # If we pressed a button,
                if pressed:
                    print("PRESSED:", row_pin, column_pin)
                    key_pressed = row_pin * 3 + column_pin

            # Set the row-output to LOW again
            GPIO.output(self.__row_pins[row_pin], GPIO.LOW)

            # Done after resetting the row pins
            if key_pressed is not None:
                return self.__keys[key_pressed]

        # Returns the key pressed
        return key_pressed

    def get_next_signal(self):
        """Pools the Keypad until a signal is pressed"""
        next_signal = None
        while True:
            prev_signal = next_signal
            next_signal = self.do_polling()

            if (next_signal != prev_signal) and prev_signal:
                return prev_signal

            # Don't want to delay unless the next signal was not found
            if not next_signal:
                time.sleep(20/1000)


class LedBoard:
    """Controls the setup and LedBoard"""

    def __init__(self):
        """Defines variables for controlling the led board"""
        # LED_KEY = [[PIN_0_IN/OUT, HIGH/LOW], [PIN_1_IN/OUT, HIGH/LOW], [PIN_2_IN/OUT, HIGH/LOW]]
        self.__led_dictionary = {
            -1: [[GPIO.IN, GPIO.LOW], [GPIO.IN, GPIO.LOW], [GPIO.IN, GPIO.LOW]],
            0:  [[GPIO.OUT, GPIO.HIGH], [GPIO.OUT, GPIO.LOW], [GPIO.IN, GPIO.LOW]],
            1:  [[GPIO.OUT, GPIO.LOW], [GPIO.OUT, GPIO.HIGH], [GPIO.IN, GPIO.LOW]],
            2:  [[GPIO.IN, GPIO.LOW], [GPIO.OUT, GPIO.HIGH], [GPIO.OUT, GPIO.LOW]],
            3:  [[GPIO.IN, GPIO.LOW], [GPIO.OUT, GPIO.LOW], [GPIO.OUT, GPIO.HIGH]],
            4:  [[GPIO.OUT, GPIO.HIGH], [GPIO.IN, GPIO.LOW], [GPIO.OUT, GPIO.LOW]],
            5:  [[GPIO.OUT, GPIO.LOW], [GPIO.IN, GPIO.LOW], [GPIO.OUT, GPIO.HIGH]],
        }

        self.__pin_dictionary = {
            0: 13,
            1: 19,
            2: 26
        }

        # Define the flash frequency in milliseconds
        self.__flash_frequency = 200

        # Define the led sleep while flash in milliseconds
        self.__led_sleep = 3

        # Define the power up animation length in milliseconds
        self.__time_power_up = 2

        # Define the power down animation length in milliseconds
        self.__time_power_down = 2

        self.setup()

    def setup(self):
        """Setup the GPIO mode"""
        GPIO.setmode(GPIO.BCM)
        self.go_dark()

    def light_led(self, index):
        """Lights a led given an index"""
        # Get the led configuration from the dictionary
        configuration = self.__led_dictionary[index]

        # Configure the led
        for pin in range(3):
            GPIO.setup(self.__pin_dictionary[pin], configuration[pin][0])
            if configuration[pin][0] == GPIO.OUT:
                GPIO.output(self.__pin_dictionary[pin], configuration[pin][1])

    def go_dark(self):
        """Turns off all lights"""
        self.light_led(-1)

    def flash_all_leds(self, seconds):
        """Flashes all the leds in the duration of the argument 'seconds'"""
        time_ms = 0
        while time_ms / 1000 < seconds:
            # Check whether the leds should be on or off
            if time_ms % (self.__flash_frequency * 2) < self.__flash_frequency:
                # Light all the leds quickly in succession
                # The human eye will not see that they are not lit at the same time
                for led in range(6):
                    self.light_led(led)
                    time.sleep(self.__led_sleep/1000)
                    time_ms += self.__led_sleep
            else:
                # Turn off all leds and leave them dark
                self.go_dark()
                time.sleep(self.__led_sleep/1000)
                time_ms += self.__led_sleep

        self.go_dark()

    def twinkle_all_leds(self, seconds, outwards=True):
        """Will move the leds from inside out in the duration of argument 'seconds'"""
        time_ms = 0
        while time_ms / 1000 < seconds:
            # Figure out which leds to light simultaneously
            led_configurations = [[0, 1], [4, 5], [2, 3]]
            time_counter = time_ms % (self.__flash_frequency * 3)
            config_index = int(math.floor(time_counter) / self.__flash_frequency)
            # Reverse the config_index if not outwards
            config_index = abs((0 if outwards else 2) - config_index)
            leds = led_configurations[config_index]

            # Light the leds quickly in succession
            # The human eye will not see that they are not lit at the same time
            for led in leds:
                self.light_led(led)
                time.sleep(self.__led_sleep/1000)
                time_ms += self.__led_sleep

        self.go_dark()

    def power_up(self):
        """Power up led-animation"""
        self.twinkle_all_leds(self.__time_power_up, True)

    def power_down(self):
        """Power down led-animation"""
        self.twinkle_all_leds(self.__time_power_down, False)


class KPC:
    def __init__(self):
        self.keypad = Keypad()
        self.led_board = LedBoard()
        self.password_file_path = "password.txt"
        self.password = read_password(self.password_file_path)
        self.cumulative_password = ""
        self.override_signal = None
        self.led_id = ""
        self.led_time = ""
        self.FSM = FSM(self)
        self.setup_rules()
        self.FSM.main_loop()

    def append_next_password_digit(self, digit):
        self.cumulative_password += digit
        print(self.cumulative_password)

    def verify_password(self, signal=None):
        if self.cumulative_password == self.password:
            self.twinkle_leds()
            self.override_signal = "Y"
        else:
            self.flash_leds()
            self.override_signal = "N"

    def reset_agent(self, signal=None):
        self.cumulative_password = ""
        self.override_signal = None
        self.led_id = ""
        self.led_time = ""

    def get_next_signal(self, signal=None):
        if self.override_signal:
            temp = self.override_signal
            self.override_signal = None
            return temp
        return self.keypad.get_next_signal()

    def verify_password_change(self, signal=None):
        if len(self.cumulative_password) >= 4:
            self.twinkle_leds()
            self.password = self.cumulative_password
            with open(self.password_file_path, "w+") as password_file:
                password_file.write(self.password)
        else:
            self.flash_leds()
        self.reset_agent()

    def set_led_id(self, led_id):
        self.led_id = led_id

    def append_led_time(self, digit):
        self.led_time += digit

    def light_one_led(self, signal=None):
        self.led_board.light_led(int(self.led_id))
        time.sleep(int(self.led_time))
        self.led_board.go_dark()
        self.reset_agent()

    def flash_leds(self, signal=None):
        self.led_board.flash_all_leds(2)

    def twinkle_leds(self, signal=None):
        self.led_board.twinkle_all_leds(2)

    def boot_down(self, signal=None):
        self.led_board.power_down()

    def boot_up(self, signal=None):
        self.led_board.power_up()
        self.reset_agent()

    def do_nothing(self, signal=None):
        pass

    def setup_rules(self):
        rules = [
            Rule(State.init, State.done, Signal.hash, KPC.do_nothing),
            Rule(State.init, State.read1, Signal.any, KPC.boot_up),

            Rule(State.read1, State.read1, Signal.digit, KPC.append_next_password_digit),
            Rule(State.read1, State.verify, Signal.asterisk, KPC.verify_password),
            Rule(State.read1, State.init, Signal.any, KPC.reset_agent),

            Rule(State.verify, State.active, Signal.yes, KPC.do_nothing),
            Rule(State.verify, State.init, Signal.any, KPC.reset_agent),

            Rule(State.active, State.read2, Signal.asterisk, KPC.reset_agent),
            Rule(State.active, State.logout, Signal.hash, KPC.do_nothing),
            Rule(State.active, State.led, Signal.any, KPC.do_nothing),

            Rule(State.read2, State.read2, Signal.digit, KPC.append_next_password_digit),
            Rule(State.read2, State.active, Signal.asterisk, KPC.verify_password_change),
            Rule(State.read2, State.active, Signal.any, KPC.reset_agent),

            Rule(State.led, State.time, Signal.led, KPC.set_led_id),
            Rule(State.led, State.active, Signal.any, KPC.reset_agent),

            Rule(State.time, State.time, Signal.digit, KPC.append_led_time),
            Rule(State.time, State.active, Signal.asterisk, KPC.light_one_led),
            Rule(State.time, State.active, Signal.any, KPC.reset_agent),

            Rule(State.logout, State.init, Signal.hash, KPC.boot_down),
            Rule(State.logout, State.active, Signal.any, KPC.reset_agent)
                ]
        for rule in rules:
            self.FSM.add_rule(rule)


def read_password(file):
    with open(file) as password_file:
        password = password_file.read().strip()
        print(password)
        return password


if __name__ == "__main__":
    GPIO.setwarnings(False)
    kpc = KPC()
