import asyncio
import math
import logging
from mavsdk import System
from dronekit import connect, VehicleMode, LocationGlobalRelative

from .link_interface import LinkInterface

# TODO Ismail, Zak unit tests
class MavLink(LinkInterface):
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

    ################# CONTROL SECTION #################
    # This section contains methods for changing various states in the flight controller

    # TODO: Create unit test
    async def arm(self):
        while not self.drone.is_armable:
            print(" Waiting for vehicle to initialise...")
            await asyncio.sleep(1)
        self.drone.mode = VehicleMode("GUIDED")
        while not self.drone.mode.name == "GUIDED":
            print("Changing to GUIDED...")
            self.drone.mode = "GUIDED"
            await asyncio.sleep(1)
        self.drone.armed = True
        while not self.drone.armed:
            print("Arming motors... Vehicle Mode: ")
            await asyncio.sleep(1)
        print("Armed!")

    # TODO: Create unit test
    async def disarm(self):
        self.drone.armed = False
        while self.drone.armed:
            print("Disarming motors... Vehicle Mode: ")
            await asyncio.sleep(1)
        print("Disarmed!")

    ################# FLIGHT SECTION #################
    # This section contains the methods for piloting the drone

    async def ascend(self, alt):
        self.status = self.STATUS_EXECUTING_COMMAND

        # Can't take off without arming
        if not self.drone.armed:
            await self.arm()
        # Ready to go!
        print("Taking off!")

        self.altitude = alt
        # Make sure takeoff happens
        self.drone.simple_takeoff(alt)
        while self.drone.mode.name != "GUIDED":
            print("Taking off | Vehicle mode: {}".format(self.drone.mode.name))
            self.drone.mode = VehicleMode("GUIDED")
            self.drone.simple_takeoff(alt)
        await self.ensure_ascend()
        # while True:
        #     print(" Altitude: ", self.drone.location.global_relative_frame.alt)
        #     # Break and return from function
        #     print(" Altitude: ", self.drone.location.global_relative_frame.alt)
        #     # Break and return from function just below target altitude.
        #     if self.drone.location.global_relative_frame.alt >= command.alt * 0.95:
        #         print("Reached target altitude: Ready for mission")
        #         break
        #     await asyncio.sleep(1)

    async def ensure_ascend(self):
        def current_distance():
            return self.altitude - self.drone.location.global_relative_frame.alt

        check = current_distance()

        await asyncio.sleep(0.25)
        if current_distance() < check:
            return current_distance()
        elif current_distance() < 0.25:  # Close enough, we're done. Goto will ensure flight altitude anyways
            self.status = self.STATUS_DONE_COMMAND
            return self.status
        else:
            self.drone.simple_takeoff(self.altitude)

    async def goto(self, geometry):
        self.status = self.STATUS_EXECUTING_COMMAND

        self.target_location = LocationGlobalRelative(geometry["lat"], geometry["lng"], geometry["alt"])
        self.drone.simple_goto(self.target_location)

        await self.ensure_goto()
        # while self.drone.mode.name == "GUIDED":  # Stop action if we are no longer in guided mode.
        #     remaining_distance = get_distance_metres(self.drone.location.global_frame, target_location)
        #     print("Distance to target: ", remaining_distance)
        #     if remaining_distance <= target_distance * 0.01:  # Just below target, in case of undershoot.
        #         print("Reached target")
        #         break
        #     time.sleep(2)

    # Ensures that the drone continues to its destination.
    async def ensure_goto(self) -> int:
        current_location = self.drone.location.global_relative_frame
        target_distance = get_distance_metres(current_location, self.target_location)

        await asyncio.sleep(0.25)
        remaining_distance = get_distance_metres(self.drone.location.global_frame, self.target_location)
        print("GOTO: Remaining Distance: {}".format(remaining_distance))
        # We will need a better method of determining arrival, maybe combine airspeed check?
        # TODO: Yes, lets do that. implement a vector transform to get absolute velocity.
        if remaining_distance < 0.75:
            self.status = self.STATUS_DONE_COMMAND
        # Ensure goto
        elif target_distance - remaining_distance < 0.5:
            self.drone.simple_goto(self.target_location)
        return self.status

    async def land(self):
        self.status = self.STATUS_EXECUTING_COMMAND
        self.drone.mode = VehicleMode("LAND")
        await self.ensure_land()

    async def ensure_land(self):
        if self.drone.mode.name == "LAND":
            if self.drone.velocity[2] < 0.05:  # It's not moving, so we've landed
                self.status = self.STATUS_DONE_COMMAND
                return self.status
        else:
            self.drone.mode = VehicleMode("LAND")

    ################# INFORMATION SECTION #################
    # This section stores methods for accessing various information from the flight controller

    # TODO: Create unit test
    async def get_heartbeat_status(self):
        return self.get_location().update({
            "Mode": self.flight_mode,
            "Battery": self.battery.remaining_percent
        })

    # TODO: Create unit test
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



# The following is utility functions for various calculations


# TODO: Create unit test
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


# TODO: Create unit test
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