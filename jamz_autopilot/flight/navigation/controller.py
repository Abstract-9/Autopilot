import asyncio

from jamz_autopilot.flight.navigation.translations.Ardupilot import Ardupilot

# Controller holds instance of link interface
# Controller manages all flight variables and pass commands to 
# link interface- in link interface we interact with dronekit
# Controller uses option lock to make one flight command go at a time
# use lock to make sure only one command happening at time



class Controller:
    def __init__(self):
        self.commands = []
        self.current_command = None
        self.operationLock = asyncio.Lock()  # this is the mutex lock

        pass

    async def initialize(self):
        # returns Controller
        # create queue, lock

        # Not sure how to establish drone
        # drone =

        pass
    
    def set_coordinates(self):
        # returns void
        # functionality implemented in Command.py
        pass

    def main_loop(self):
        while True:
            if len(self.commands) == 0:
                # Case: All commands have been executed
                await asyncio.sleep(1)

            elif self.commads and not self.operationLock.locked():
                await self.operationLock.acquire()
                self.current_command = self.commands.pop(0)
                try:
                    # drone is supposedly initialized in initialize()
                    asyncio.create_task(drone.execute_command(self.current_command))
                finally:
                    await self.operationLock.acquire()
                    self.operationLock.release()

