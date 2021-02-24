import asyncio
from jamz_autopilot.flight.navigation.translation import Ardupilot

# TODO Jonathan unit tests
class FlightEvent(asyncio.Event):

    # TODO: Create unit test
    def __init__(self, controller_instance):
        super(FlightEvent, self).__init__()
        self.battery = None
        self.lat = None
        self.lon = None
        self.alt = None
        self.controller_instance = controller_instance

        # Give the flight controller communications interface some time to initialize before querying it
        asyncio.get_event_loop().call_later(5, self.update_vital_info)

    # TODO: Create unit test
    def update_vital_info(self):
        vitals = self.controller_instance.translator.get_vital_info()

        self.battery = vitals.Battery
        self.lat = vitals.lat
        self.lon = vitals.lon
        self.alt = vitals.alt

        loop = asyncio.get_event_loop()
        self.set()
        loop.call_later(1, self.update_vital_info)