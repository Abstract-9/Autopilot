import asyncio
import time
import functools
import os
import signal

from ..communications import Communications, CommunicationsEvent
from ..flight import Flight, FlightEvent

class Core:
    
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

    
    async def onFlightEvent(self, flightEvent : FlightEvent):
        #return none

        #process
       while True:
            await flightEvent.wait()


            #do stuff
            flightEvent.reset()


    async def onCommsEvent(self, commsEvent : CommunicationsEvent):
        #return none
        
        #process
        while True:
            await commsEvent.wait()


            #do stuff
            commsEvent.reset()


async def main():

    core = Core()

    loop = asyncio.get_event_loop()



    Communications(loop)
    Flight(loop)

    



    # try:
    #     while(1):
    #         loop.run_until_complete(core.onFlightEvent())
    #         loop.run_until_complete(core.onCommsEvent())
    #     Communications(loop)
    #     Flight(loop)
    # finally:
    #     loop.close()

    


# Python 3.7+
asyncio.run(main())