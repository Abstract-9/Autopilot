import asyncio

from .translation import Ardupilot
from .flight_event import FlightEvent

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

    def __init__(self, device=None):

        self._commands = []
        self.current_command = None
        if device:
            self.device = device

        # Initialize synchronization primitives
        self.commands_lock = asyncio.Lock()
        self.operation_lock = asyncio.Lock()

        # Initialize hardware translator
        self.translator = Ardupilot(self.device)

        asyncio.get_event_loop().create_task(self.command_loop())

    async def command_loop(self):
        if len(self._commands) == 0:
            # Case: All commands have been executed
            await asyncio.sleep(0.5)

        elif self._commands and not self.operation_lock.locked():
            self.current_command = await self.pop_command()

            await self.operation_lock.acquire()
            try:
                asyncio.create_task(self.translator.execute_command(self.current_command, self.operation_lock))
            finally:
                # When the flight operation is complete, it will release the operation lock.
                # This blocks until that happens.
                await self.operation_lock.acquire()
                self.operation_lock.release()

        # Schedule callback
        await asyncio.sleep(0.5)
        asyncio.get_event_loop().create_task(self.command_loop())

    async def push_command(self, command):
        await self.commands_lock.acquire()
        self._commands.append(command)
        self.commands_lock.release()

    async def pop_command(self):
        await self.commands_lock.acquire()
        command = self._commands.pop()
        self.commands_lock.release()
        return command
