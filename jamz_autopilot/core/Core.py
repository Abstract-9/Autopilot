import asyncio
import time
import functools
import os
import signal

from ..communications import Communications, CommunicationsEvent
from ..flight import Flight, FlightEvent


class Core:

    config = {
        "battery" : None,
        "lat" : None,
        "long" : None,
        "alt" : None
    }

    instance = None
    flight = None
    comms = None

    @staticmethod 
    def getInstance():
      
        if Core.instance == None:
            Core()
        return Core.instance


    def __init__(self):
      
        if Core.instance != None:
            raise Exception("This Class is a Singleton!")
        else:
            Core.instance = self


    async def initializeFlight(self, loop):
        #process
        #self.flightEvent = Flight()
        self.flight = Flight(loop)
        return self.flight
    

    async def initializeComms(self, loop):
        #process
        #self.commsEvent = Communications()
        self.comms = Communications(loop)
        return self.comms

    
    async def onFlightEvent(self, flightEvent : FlightEvent):
        #return none

        #process
        while True:
            await flightEvent.wait()

            self.config["battery"] = flightEvent.battery
            self.config["lat"] = flightEvent.lat
            self.config["long"] = flightEvent.long
            self.config["alt"] = flightEvent.alt

            #do stuff
            flightEvent.reset()


    async def onCommsEvent(self, commsEvent : CommunicationsEvent):
        #return none
        
        #process
        while True:
            await commsEvent.wait()

            self.flight.commands.append(commsEvent.command)

            #do stuff
            commsEvent.reset()


async def main():

    core = Core.getInstance()

    loop = asyncio.get_event_loop()

    core.initializeComms(loop)
    core.initializeFlight(loop)
    
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