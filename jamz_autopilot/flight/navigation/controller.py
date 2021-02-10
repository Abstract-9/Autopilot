import asyncio

from jamz_autopilot.flight.navigation.translations. import

# Controller holds instance of link interface
# Controller manages all flight variables and pass commands to 
# link interface- in link interface we interact with dronekit
# Controller uses option lock to make one flight command go at a time
# use lock to make sure only one command happening at time

operationLock = asyncio.Lock() # this is the mutex lock

class Controller:
    def __init__(self):
        pass

    async def initialize(self):
        # returns Controller
        # create queue, lock

        pass
    
    def set_coordinates(self):
        # returns void
        pass

    def main_loop(self):
