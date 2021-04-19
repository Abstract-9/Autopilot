import asyncio
from .communications import Communications
from .flight.navigation import FlightController

async def main():

    loop = asyncio.get_event_loop()

    comms = Communications(loop, False)
    flight_con = FlightController(loop)

    comms.flight_controller = flight_con

    # try:
    #     while(1):
    #         loop.run_until_complete(core.onFlightEvent())
    #         loop.run_until_complete(core.onCommsEvent())
    #     Communications(loop)
    #     Flight(loop)
    # finally:
    #     loop.close()


# Python 3.7+, only run if this is the main interpreter
if __name__ == "__main__":
    asyncio.run(main())
