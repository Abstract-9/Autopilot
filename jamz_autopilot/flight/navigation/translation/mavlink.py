import asyncio
import math
import logging
from mavsdk import System


class MavLink:
    # Create pre-defined flight status objects
    STATUS_IDLE = 0
    STATUS_DONE_COMMAND = 1
    STATUS_EXECUTING_COMMAND = 2

    # Define drone ground speed in m/s.
    GROUND_SPEED = 1
    # Define the amount of time that the drone can continue its mission without talking to the controller.
    NETWORK_TIMEOUT = 120  # 120 seconds

    is_ready = asyncio.Event()

    logger = logging.getLogger(__name__)

    ################# INFORMATION SECTION #################
    # This section stores methods for accessing various information from the flight controller

    def get_heartbeat_status(self):
        return self.get_location().update({
            "Mode": self.flight_mode,
            "Battery": self.battery.remaining_percent
        })

    def get_location(self):
        return {
            "lat": self.location.latitude_deg,
            "lng": self.location.longitude_deg,
            "alt": self.location.absolute_altitude_m
        }

    # The following methods are used to subscribe to various drone status updates

    async def sub_battery(self):
        async for battery in self.drone.telemetry.battery():
            self.battery = battery.remaining_percent

    async def sub_location(self):
        async for location in self.drone.telemetry.position():
            self.location = location

    async def sub_flight_mode(self):
        async for mode in self.drone.telemetry.flight_mode():
            self.flight_mode = mode.name

    ################# Utility section #################
    # This section contains various utility and I/O methods

    def __init__(self, device):
        self.drone = System()
        self.battery = None
        self.location = None
        self.flight_mode = None
        self.home_location = None

        asyncio.create_task(self._initialize(device))

    # For async initialization needs
    async def _initialize(self, device):
        await self.drone.connect(device)

        self.logger.info("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"Drone discovered!")
                break

        self.logger.info("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok:
                print("Global position estimate ok")
                break

        self.logger.info("Retrieving home location...")
        async for home in self.drone.telemetry.home():
            self.home_location = home
            break

        # Variables for controlling flight
        self.altitude = 0
        self.target_location = None
        self.status = self.STATUS_IDLE

        # Subscribe to necessary info feeds
        asyncio.create_task(self.sub_battery())
        asyncio.create_task(self.sub_location())

        self.logger.info("MAVSdk initialization complete! Home location: %s" % self.home_location)
        self.is_ready.set()


"""
The following is utility functions for various calculations
"""

def get_distance_metres(location1, location2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = location2.lat - location1.lat
    dlong = location2.lon - location1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5

def get_bearing(location1, location2):
    """
    Returns the bearing between the two LocationGlobal objects passed as parameters.

    This method is an approximation, and may not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    off_x = location2.lon - location1.lon
    off_y = location2.lat - location1.lat
    bearing = 90.00 + math.atan2(-off_y, off_x) * 57.2957795
    if bearing < 0:
        bearing += 360.00
    return bearing