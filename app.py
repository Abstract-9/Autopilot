import asyncio
from threading import Thread
from jamz_autopilot.communications import Client
from jamz_autopilot.flight.navigation import FlightController


class App:

    comms_event_loop = asyncio.new_event_loop()
    flight_con_event_loop = asyncio.new_event_loop()

    def _start_comms(self) -> None:
        asyncio.set_event_loop(self.comms_event_loop)
        Client()

    def _start_flight_con(self) -> None:
        asyncio.set_event_loop(self.flight_con_event_loop)
        FlightController()

    def __init__(self):

        t_comms = Thread(target=self._start_comms, args=(self.comms_event_loop,) )
        self._start_comms()
        self._start_flight_con()

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
    App()
