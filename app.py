import asyncio
from jamz_autopilot.communications import Client
from jamz_autopilot.flight.navigation import FlightController


class App:

    comms = None
    flight_con = None

    def __init__(self):

        Client()
        FlightController()

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
    asyncio.get_event_loop().run_forever()

# Python 3.7+, only run if this is the main interpreter
if __name__ == "__main__":
    asyncio.run(_main())
