import asyncio
import time
import functools
import os
import signal

from ..communications import Communications, CommandEvent
from ..flight.navigation import FlightController, FlightEvent


class Core:

    config = {
        "battery": None,
        "lat": None,
        "long": None,
        "alt": None
    }

    instance = None
    flight = None
    comms = None

    @staticmethod 
    def get_instance():
      
        if Core.instance is None:
            Core()
        return Core.instance

    def __init__(self):
      
        if Core.instance is not None:
            raise Exception("This Class is a Singleton!")
        else:
            Core.instance = self

    async def initialize_flight(self, loop):
        self.flight = FlightController(loop)
        return self.flight

    async def initialize_comms(self, loop):
        self.comms = Communications(loop, False)
        return self.comms

    async def on_flight_event(self, flight_event: FlightEvent):

        while True:
            await flight_event.wait()

            self.config["battery"] = flight_event.battery
            self.config["lat"] = flight_event.lat
            self.config["long"] = flight_event.long
            self.config["alt"] = flight_event.alt

            flight_event.reset()

    async def on_comms_event(self, comms_event: CommandEvent):

        while True:
            await comms_event.wait()

            self.flight.commands.append(comms_event.command)

            comms_event.reset()


async def main():

    core = Core.get_instance()

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