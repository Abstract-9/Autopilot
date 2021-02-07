import asyncio
import time
import functools
import os
import signal

from ..communications import Communications
from ..flight import Flight

class Core:

    flightEvent = 0 #asyncio.Event
    commsEvent = 0 #asyncio.Event
    
    def __init__(self):
        pass


    async def initializeFlight(self):
        #return Autopilot object

        #process
        self.flightEvent = Flight()
        


    async def initializeComms(self):
        #return Comms object

        #process
        self.commsEvent = Communications()

    
    async def onFlightEvent(self):
        #return none

        #process
        pass


    async def onCommsEvent(self):
        #return none
        
        #process
        pass



async def main():

    core = Core()

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(core.onFlightEvent())
        loop.run_until_complete(core.onCommsEvent())
    finally:
        loop.close()


    


# Python 3.7+
asyncio.run(main())