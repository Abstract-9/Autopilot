import asyncio

from translation import Ardupilot

# Controller holds instance of link interface
# Controller manages all flight variables and pass commands to 
# link interface- in link interface we interact with dronekit
# Controller uses option lock to make one flight command go at a time
# use lock to make sure only one command happening at time


class FlightController:

    # How to connect to the hardware flight controller. Some examples;
    # "/dev/ttyACM0" Serial interface over USB
    # "tcp://127.0.0.1:6603" Local TCP connection
    # "udp://127.0.0.1:5202" Local UDP connection
    device = "/dev/ttyACM0"

    def __init__(self):
        self.commands = []
        self.current_command = None
        self.operation_lock = asyncio.Lock()  # this is the mutex lock
        self.translator = Ardupilot(self.device)
        pass
    
    def set_coordinates(self):
        # returns void
        # functionality implemented in command.py
        pass

    def main_loop(self):
        if len(self.commands) == 0:
            # Case: All commands have been executed
            await asyncio.sleep(0.5)

        elif self.commands and not self.operation_lock.locked():
            await self.operation_lock.acquire()
            self.current_command = self.commands.pop(0)
            try:
                # drone is supposedly initialized in initialize()
                asyncio.create_task(self.translator.execute_command(self.current_command, self.operation_lock))
            finally:
                await self.operation_lock.acquire()
                self.operation_lock.release()

        # Schedule callback
        asyncio.get_event_loop().call_later(0.5, self.main_loop)

