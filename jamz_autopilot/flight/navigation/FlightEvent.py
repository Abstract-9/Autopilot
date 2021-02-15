import asyncio
from jamz_autopilot.flight.navigation.translations.Ardupilot import Ardupilot

class FlightEvent(asyncio.Event):

    def __init__(self):
        super(FlightEvent, self).__init__()
        self.battery = None
        self.lat = None
        self.lon = None
        self.alt = None

        self.update_vital_info()


    def update_vital_info(self):

        vitals = Ardupilot.get_vital_info()

        self.battery = vitals.Battery
        self.lat = vitals.lat
        self.lon = vitals.lon
        self.alt = vitals.alt

        loop = asyncio.get_event_loop()
        self.set()
        loop.call_later(1, self.update_vital_info)