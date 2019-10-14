from keypad import Keypad
from ledboard import *


class Rule:
    def __init__(self, state, next_state, signal_check, action):
        self.state = state
        self.next_state = next_state
        self.action = action
        self.signal_check = signal_check

    def do_action(self, signal):
        return self.action(signal)


class State:
    init = 0
    read1 = 2
    read2 = 3  # need two reads to represent both state where kpc is not initialized and state where it actually reads
    read_password = 1
    read_active = 2
    logout = 3
    verify = 4
    active = 5
    time = 6
    led_config = 7


class Signal:
    """ Signal"""
    @staticmethod
    def all_symbols(signal):
        """all"""
        return True

    @staticmethod
    def all_digits(signal):
        """dig"""
        return ord("0") <= ord(signal) <= ord("9")

    @staticmethod
    def asterisk(signal):
        """asterisk"""
        return signal == "*"

    @staticmethod
    def correct(signal):
        """correct"""
        return signal == "Y"

    @staticmethod
    def wrong(signal):
        """wrong"""
        return signal == "N"

    @staticmethod
    def hash(signal):
        """hash"""
        return signal == "#"

    @staticmethod
    def led_digits(signal):
        """led"""
        return ord("0") <= ord(signal) <= ord("5")

class KPC_Agent:
    """ KPC_Agent"""
    def __init__(self):
        self.fsm = FSM(self)
        self.keypad = Keypad()
        self.led = LEDboard()
        self.file_name = "passord.txt"
        self.password_buffer = ""
        self.override_signal = None
        self.led_id = ''
        self.led_duration = ''
        self.Legal_numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    def init_passcode_entry(self, signal=None):
        """ init"""
        print('init passcode entry')
        self.led.power_up()
        # flash

    def reset_agent(self, signal=None):
        """ reset"""
        self.password_buffer = ""
        self.led_id = ""
        self.led_duration = ""
        self.override_signal = None

    def get_next_signal(self, signal=None):
        """ get next signal"""
        if self.override_signal:
            result = self.override_signal
            self.override_signal = None
            return result

        result = None
        while not result:
            result = self.keypad.poll_buttons()
        if result:
            print(self.password_buffer)
        return result

    def verify_login(self, signal=None):
        """ verify"""
        if self.password_buffer == self.read_password_file(self.file_name): ##lese fra fil
            self.override_signal = "Y"
            self.led.correct()
        else:
            self.override_signal = "N"
            self.led.wrong()
            self.init_passcode_entry()

    def add_next_digit(self, digit):
        """ add-next_digit"""
        print('adding digit, maybe', digit)
        if digit in self.Legal_numbers:
            print("added:", digit)
            self.password_buffer += digit

    def validate_password_change(self, signal=None):
        validate = True
        if len(self.password_buffer) < 4:
            validate = False
        for num in self.password_buffer:
            if num not in self.Legal_numbers:
                validate = False
        if validate:
            with open(self.file_name, "w+") as password_file:
                password_file.write(self.password_buffer)
        self.reset_agent()

    def read_password_file(self, file):
        """ read"""
        with open(file) as password_file:
            password = password_file.read().strip()
            print(password)
            return password

    def light_one_led(self, signal=None):
        """one led"""
        print("inne i et lys")
        self.led.lid_ldur(int(self.led_id), int(self.led_duration))
        self.reset_agent()

    def exit_action(self, signal=None):
        """ exit"""
        self.led.power_down()

    def test(self):
        """ test"""
        print("testing passcode entry")
        self.init_passcode_entry()

    def do_nothing(self, signal=None):
        """ nothing"""
        pass

    def set_led(self, signal):
        """ set led"""
        self.led_id = signal

    def append_time(self, signal):
        """ append"""
        print("appender tid", signal)
        self.led_duration += signal


class FSM:
    """FSM"""

    def __init__(self, agent):
        self.agent = agent
        self.rule_list = []
        self.signal = None
        self.state = State.init

    def setup_rules(self):
        """ setup"""
        self.rule_list = [
            Rule(State.init, State.read_password, Signal.all_symbols, self.agent.init_passcode_entry),
            Rule(State.read_password, State.read_password, Signal.all_digits, self.agent.add_next_digit),
            Rule(State.read_password, State.verify, Signal.asterisk, self.agent.verify_login),
            Rule(State.read_password, State.init, Signal.all_symbols, self.agent.reset_agent),

            Rule(State.verify, State.active, Signal.correct, self.agent.do_nothing),
            Rule(State.verify, State.init, Signal.all_symbols, self.agent.reset_agent),

            Rule(State.active, State.read_active, Signal.asterisk, self.agent.reset_agent),
            Rule(State.active, State.logout, Signal.hash, self.agent.exit_action),
            Rule(State.active, State.led_config, Signal.all_symbols, self.agent.do_nothing),

            Rule(State.read_active, State.read_active, Signal.all_digits, self.agent.add_next_digit),
            Rule(State.read_active, State.active, Signal.asterisk, self.agent.validate_password_change),
            Rule(State.read_active, State.active, Signal.all_symbols, self.agent.reset_agent),

            Rule(State.led_config, State.time, Signal.led_digits, self.agent.set_led),
            Rule(State.led_config, State.active, Signal.all_symbols, self.agent.reset_agent),

            Rule(State.time, State.time, Signal.all_digits, self.agent.append_time),
            Rule(State.time, State.active, Signal.asterisk, self.agent.light_one_led),
            Rule(State.time, State.active, Signal.all_symbols, self.agent.reset_agent),

            Rule(State.logout, State.init, Signal.hash, self.agent.exit_action),
            Rule(State.logout, State.active, Signal.all_symbols, self.agent.reset_agent)
        ]

    def add_rule(self, rule):
        """ add"""
        self.rule_list.append(rule)

    def get_next_signal(self):
        """next"""
        return self.agent.get_next_signal()

    def run_rules(self, state, signal):
        """run_rules"""
        print("RUN RULES:", signal)
        for rule in self.rule_list:
            if rule.state == state and rule.signal_check(signal):
                self.state = rule.next_state
                self.fire_rule(rule, signal)
                break

    def main_loop(self):
        """main"""
        while True:
            self.run_rules(self.state, self.get_next_signal())

    def fire_rule(self, rule, signal):
        """ fire"""
        rule.do_action(signal)
