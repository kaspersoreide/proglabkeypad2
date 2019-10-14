from FSM import *

def main():
    agent = KPC_Agent()
    agent.fsm.setup_rules()
    agent.fsm.main_loop()

main()
