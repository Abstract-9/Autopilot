
from dronekit import connect, VehicleMode, LocationGlobalRelative
from jamz_autopilot.flight.navigation.Controller import Controller
import asyncio
from . import FlightStatus

class Ardupilot(Controller):
    # Create pre-defined flight status objects
    STATUS_IDLE = FlightStatus(0)
    STATUS_DONE_COMMAND = FlightStatus(1)
    STATUS_EXECUTING_COMMAND = FlightStatus(2)

    # Define drone default altitude. It'll be much higher in prod
    DEFAULT_ALTITUDE = 5
    # Define drone ground speed in m/s.
    GROUND_SPEED = 1
    # Define the amount of time that the drone can continue its mission without talking to the controller.
    NETWORK_TIMEOUT = 120  # 120 seconds

    ################# CONTROL SECTION #################
    # This section contains methods for changing various states in the flight controller

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

    async def disarm(self):
        self.drone.armed = False
        while self.drone.armed:
            print("Disarming motors... Vehicle Mode: ")
            await asyncio.sleep(1)
        print("Disarmed!")


    def __init__(self):
        pass

    def goto(self):
        # returns void
        pass

    def ascend(self):
        # returns void
        pass

    def descend(self):
        # returns void
        pass
    