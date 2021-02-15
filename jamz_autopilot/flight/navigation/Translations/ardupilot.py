
from dronekit import connect, VehicleMode, LocationGlobalRelative
from jamz_autopilot.flight.navigation.Controller import Controller
import asyncio
from . import FlightStatus

class Ardupilot(Controller):
    # Create pre-defined flight status objects
    STATUS_IDLE = FlightStatus(0)
    STATUS_DONE_COMMAND = FlightStatus(1)
    STATUS_EXECUTING_COMMAND = FlightStatus(2)

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

    ################# FLIGHT SECTION #################
    # This section contains the methods for piloting the drone

    async def ascend(self, command):
        self.status = self.STATUS_EXECUTING_COMMAND

        # Can't take off without arming
        if not self.drone.armed:
            await self.arm()
        # Ready to go!
        print("Taking off!")

        self.altitude = command.alt
        # Make sure takeoff happens
        self.drone.simple_takeoff(command.alt)
        while self.drone.mode.name != "GUIDED":
            print("Taking off | Vehicle mode: {}".format(self.drone.mode.name))
            self.drone.mode = VehicleMode("GUIDED")
            self.drone.simple_takeoff(command.alt)
        command.wasExecuted = True
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

    async def goto(self, command):
        self.status = self.STATUS_EXECUTING_COMMAND

        self.target_location = LocationGlobalRelative(command.lat, command.lon, command.alt)
        self.drone.simple_goto(self.target_location)

        command.wasExecuted = True
        await self.ensure_goto()
        # while self.drone.mode.name == "GUIDED":  # Stop action if we are no longer in guided mode.
        #     remaining_distance = get_distance_metres(self.drone.location.global_frame, target_location)
        #     print("Distance to target: ", remaining_distance)
        #     if remaining_distance <= target_distance * 0.01:  # Just below target, in case of undershoot.
        #         print("Reached target")
        #         break
        #     time.sleep(2)

    # Ensures that the drone continues to its destination.
    async def ensure_goto(self):
        current_location = self.drone.location.global_relative_frame
        target_distance = get_distance_metres(current_location, self.target_location)

        await asyncio.sleep(0.25)
        remaining_distance = get_distance_metres(self.drone.location.global_frame, self.target_location)
        print("GOTO: Remaining Distance: {}".format(remaining_distance))
        if remaining_distance < target_distance:  # If this is true, goto is working.
            return remaining_distance

        # We will need a better method of determining arrival, maybe combine airspeed check?
        # TODO: Yes, lets do that. implement a vector transform to get absolute velocity.
        elif remaining_distance < 0.75:
            self.status = self.STATUS_DONE_COMMAND
            return self.status

        # Ensure goto
        else:
            self.drone.simple_goto(self.target_location)

    async def descend(self, command):
        self.status = self.STATUS_EXECUTING_COMMAND
        self.drone.mode = VehicleMode("descend")
        command.wasExecuted = True
        await self.ensure_descend()

    async def ensure_descend(self):
        if self.drone.mode.name == "descend":
            if self.drone.velocity[2] < 0.05:  # It's not moving, so we've descended
                self.status = self.STATUS_DONE_COMMAND
                return self.status
        else:
            self.drone.mode = VehicleMode("descend")

    # Command mapping. There's definitely a better way to do this.
    async def execute_command(self, command, operationLock):
        # Command bindings
        command_bindings = {
            Command.GOTO: [self.goto, self.ensure_goto],
            Command.ASCEND: [self.ascend, self.ensure_ascend],
            Command.DESCEND: [self.descend, self.ensure_descend],
            Command.RTL: self.return_home
        }

        if not command.wasExecuted:
            await command_bindings[command.command][0](command)
        else:
            await command_bindings[command.command][1]()

        if self.status == self.STATUS_DONE_COMMAND:
            operationLock.release()
        loop = asyncio.get_event_loop()
        loop.call_later(1, self.execute_command, command, operationLock)

    ################# INFORMATION SECTION #################
    # This section stores methods for accessing various information from the flight controller

    def get_status(self):
        return {
            "GPS": self.drone.gps_0,
            "Battery": self.drone.battery,
            "Last Heartbeat": self.drone.last_heartbeat,
            "Armable": self.drone.is_armable,
            "Status": self.drone.system_status.state,
            "Mode": self.drone.mode,
            "Altitude": self.drone.location.global_relative_frame.alt
        }

    def get_location(self):
        return {
            "lat": self.drone.location.global_relative_frame.lat,
            "lon": self.drone.location.global_relative_frame.lon,
            "alt": self.drone.location.global_relative_frame.alt
        }

    def get_vital_info(self):
        return {
            "lat": self.drone.location.global_relative_frame.lat,
            "lon": self.drone.location.global_relative_frame.lon,
            "alt": self.drone.location.global_relative_frame.alt,
            "Battery": self.drone.battery,
        }

    ################# Utility section #################
    # This section contains various utility and I/O methods

    def send_heartbeat(self):
        try:
            data = self.get_location().update(
                {"state": self.drone.system_status.state,
                 "mode": self.drone.mode.name,
                 "velocity": self.drone.velocity,
                 "heading": self.drone.heading})
            response = requests.post("%s/drones/%d/heartbeat" % (self.controller, self.drone_id), data=data)
        except Exception as e:
            print("uh oh, can't reach home. Keep flying for now...")
            self.time_without_network += 5
            if self.time_without_network == self.NETWORK_TIMEOUT:
                print("network timeout reached. Returning home.")
                self.return_home()
            return
        if response.status_code == 505:
            # 505 means we need to change our ID. This should almost never happen
            self.drone_id = response.json()['id']

    def close_connection(self):
        self.drone.close()

    def __init__(self, device, drone_id, home):
        self.drone = connect(device)
        print("Drone connected!")
        # Variables for talking to the controller
        self.drone_id = drone_id
        self.controller = home
        self.commands = []
        # Variables for controlling network timeout
        self.heartbeat_counter = 0
        self.time_without_network = 0
        # Wait for flight controller to be ready
        self.drone.wait_ready()
        cmds = self.drone.commands
        cmds.download()
        cmds.wait_ready()

        # Setup initial flight params
        self.drone.groundspeed = self.GROUND_SPEED

        # Variables for controlling flight
        self.altitude = 0
        self.target_location = None
        self.status = self.STATUS_IDLE
        self.home_location = self.drone.home_location
        while self.home_location is None:
            self.home_location = self.drone.home_location

        print("Ready to go! Home location: %s" % self.home_location)

    # The following is utility functions for various calculations

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