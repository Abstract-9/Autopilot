import asyncio

from jamz_autopilot.flight.navigation.translation.ardupilot import Ardupilot
from jamz_autopilot.flight.navigation.flight_event import FlightEvent
from jamz_autopilot.core.core import Core

# Controller holds instance of link interface
# Controller manages all flight variables and pass commands to 
# link interface- in link interface we interact with dronekit
# Controller uses option lock to make one flight command go at a time
# use lock to make sure only one command happening at time

# TODO Omar unit tests
class FlightController:

    # How to connect to the hardware flight controller. Some examples;
    # "/dev/ttyACM0" Serial interface over USB
    # "tcp://127.0.0.1:6603" Local TCP connection
    # "udp://127.0.0.1:5202" Local UDP connection
    device = "/dev/ttyACM0"

    # TODO: Create unit test
    def __init__(self, device=None):
        # Import upon construction to avoid circular imports
        from jamz_autopilot.core import Core

        self.commands = []
        self.current_command = None
        if device:
            self.device = device
        self.operation_lock = asyncio.Lock()  # this is the mutex lock
        self.translator = Ardupilot(self.device)

        Core.get_instance().on_flight_event(FlightEvent(self))
        asyncio.get_event_loop().create_task(self.main_loop())

    # TODO: Create unit test
    async def main_loop(self):
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
        await asyncio.sleep(0.5)
        asyncio.get_event_loop().create_task(self.main_loop())

