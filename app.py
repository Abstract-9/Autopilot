import asyncio
from jamz_autopilot.communications import Client
from jamz_autopilot.flight.navigation import FlightController


class App:

    comms = None
    flight_con = None

    def __init__(self):

        self.comms = Client(self)
        self.flight_con = FlightController(self)
        # try:
        #     while(1):
        #         loop.run_until_complete(core.onFlightEvent())
        #         loop.run_until_complete(core.onCommsEvent())
        #     Communications(loop)
        #     Flight(loop)
        # finally:
        #     loop.close()


async def _main():
    App()

# Python 3.7+, only run if this is the main interpreter
if __name__ == "__main__":
    asyncio.ensure_future(_main())
    asyncio.get_event_loop().run_forever()
