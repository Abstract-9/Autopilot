import asyncio

import logging

from .translation import MavLink
from .message_broker import MessageBroker

# Controller holds instance of link interface
# Controller manages all flight variables and pass commands to
# link interface- in link interface we interact with dronekit
# Controller uses option lock to make one flight command go at a time
# use lock to make sure only one command happening at time


class FlightController:

    # How to connect to the hardware flight controller. Some examples;
    # "/dev/ttyACM0" Serial interface over USB
    # "tcp:127.0.0.1:5760" Local TCP connection
    # "udp:127.0.0.1:5202" Local UDP connection
    device = "tcp:172.22.178.64:5760"

    logger = logging.getLogger(__name__)

    # Some constants for state management

    STATE_IDLE = 0
    STATE_TAKEOFF = 1
    STATE_LANDING = 2
    STATE_IN_FLIGHT = 3
    STATE_IN_PICKUP = 4
    STATE_IN_DELIVERY = 5

    def __init__(self, app, device=None):

        # Variables for flight management
        self.state = self.STATE_IDLE
        self.has_bay_clearance = False
        self.has_path_clearance = False
        self.on_job = False
        self.whole_job = None
        self.current_job_part = None
        self.bay = None
        self.current_path = None

        # Use custom connection string if supplied
        if device:
            self.device = device

        # Initialize synchronization primitives
        self.commands_lock = asyncio.Lock()
        self.operation_lock = asyncio.Lock()

        # Initialize hardware translator
        self.translator = MavLink(self.device)

        # Message Broker
        self.message_broker = MessageBroker(app)

        asyncio.create_task(self._initialize())


    # For async initialization needs
    async def _initialize(self):
        # Wait for the mavlink connection to be active
        await self.translator.is_ready.wait()

        # Request a landingBay spot
        location = self.translator.get_location()
        while self.bay is None:
            await self.get_bay_assignment(location)
            await asyncio.sleep(0.25)

        asyncio.create_task(self.main_loop())

    # Genuinely, the thick of the logic.
    # Handle how to fly. Designed as a state machine, with decision trees under each state.
    async def main_loop(self):
        if self.state == self.STATE_IDLE:
           await self.idle_state_actions()
        elif self.state == self.STATE_TAKEOFF:
            await self.takeoff_state_actions()
        elif self.state == self.STATE_LANDING:
            await self.landing_actions()
        elif self.state == self.STATE_IN_FLIGHT:
            await self.flight_actions()
        elif self.state == self.STATE_IN_DELIVERY:
            await self.delivery_actions()
        elif self.state == self.STATE_IN_PICKUP:
            await self.pickup_actions()

        self.log_state()
        # Schedule callback
        await asyncio.sleep(0.5)
        asyncio.create_task(self.main_loop())

    async def idle_state_actions(self):
        # IDLE + on_job = waiting to take off
        if self.on_job:
            if not self.current_path:
                await self.handle_next_path()
            else:
                if not self.has_bay_clearance:
                    await self.get_bay_clearance()
                else:
                    self.set_state(self.STATE_TAKEOFF)
        else:
            job_message = await self.message_broker.get_message_by_event_type("JobAssignment")
            if job_message is not None:
                self.logger.info("Received Job ")
                self.whole_job = job_message["job_waypoints"]
                self.current_job_part = 0
                self.on_job = True

    async def takeoff_state_actions(self):
        if self.has_bay_clearance:
            await self.translator.drone.action.arm()
            await self.translator.drone.action.set_takeoff_altitude(self.current_path["start"]["alt"])
            await self.translator.drone.action.takeoff()
            await self.message_broker.ensure_bay_cleared(self.bay["id"])
            self.set_state(self.STATE_IN_FLIGHT)

    async def landing_actions(self):
        if self.has_bay_clearance:
            await self.translator.drone.action.land()
            await self.translator.drone.action.disarm()
            self.set_state(self.STATE_IDLE)
        else:
            await self.get_bay_clearance()

    async def flight_actions(self):
        await self.translator.drone.action.goto_location(
            self.whole_job[self.current_job_part]["lat"],
            self.whole_job[self.current_job_part]["lng"],
            self.translator.home_location.absolute_altitude_m + self.whole_job[self.current_job_part]["alt"])
        self.current_path = None
        if self.on_job:
            part_type = self.whole_job[self.current_job_part]["type"]
            if part_type == "delivery":
                self.set_state(self.STATE_IN_DELIVERY)
            else:
                self.set_state(self.STATE_IN_PICKUP)
        else:
            self.set_state(self.STATE_LANDING)

    async def delivery_actions(self):
        self.current_job_part += 1
        await self.handle_next_path()
        await asyncio.sleep(5)
        while self.current_path is None:
            await asyncio.sleep(5)
        self.set_state(self.STATE_IN_FLIGHT)

    async def pickup_actions(self):
        self.current_job_part += 1
        await self.handle_next_path()
        await asyncio.sleep(5)
        while self.current_path is None:
            await asyncio.sleep(5)
        self.set_state(self.STATE_IN_FLIGHT)

    # Super important, call this method before setting sub-states!
    def set_state(self, state):
        # Reset state-dependent booleans (sub_states)
        # self.has_bay_clearance = False

        # Set the state
        self.state = state

    async def handle_next_path(self):
        # check if we need to send a path proposal
        path_assignment = await self.message_broker.get_message_by_event_type("PathAssignment")
        if path_assignment is None and not self.message_broker.waiting_on_path_proposal:
            location = self.translator.get_location()
            # check if we're done our job
            self.check_job_state()
            destination = None
            if not self.on_job and self.bay is None:
                # Check if we need landing bay assignment
                await self.get_bay_assignment(location)
            elif not self.on_job:
                destination = {"lat": self.bay["geometry"]["lat"], "lng": self.bay["geometry"]["lng"]}
            else:
                current_job_part = self.whole_job[self.current_job_part]
                destination = \
                    {"lat": current_job_part["geometry"]["lat"], "lng": current_job_part["geometry"]["lng"]}

            if destination is not None:
                path_proposal = self.message_broker.generate_path_proposal(
                    {"lat": location["lat"], "lng": location["lng"]},
                    destination
                )
                await self.message_broker.send_message(path_proposal)
        elif path_assignment is not None:
            self.current_path = path_assignment

    async def get_bay_assignment(self, location):
        bay_assignment = await self.message_broker.get_message_by_event_type("BayAssignment")
        if bay_assignment is None and not self.message_broker.waiting_on_bay_assignment:
            await self.message_broker.send_message(self.message_broker.generate_assignment_request(location))
        elif bay_assignment is not None:
            self.bay = bay_assignment["bay"]

    async def get_bay_clearance(self):
        bay_clearance_granted = await self.message_broker.get_message_by_event_type("AccessGranted")
        if bay_clearance_granted is None and not self.message_broker.waiting_on_bay_access:
            await self.message_broker.send_message(
                self.message_broker.generate_access_request(self.bay["id"]))
        elif bay_clearance_granted is not None:
            # Assign bay clearance, but remove the bay_id since we're leaving
            self.bay = None
            self.has_bay_clearance = True

    def check_job_state(self):
        if self.current_job_part >= len(self.whole_job):
            self.on_job = False

    def get_transmittable_status(self):
        status = self.translator.get_heartbeat_status()
        status["Flight_Controller_State"] = self.state_as_string()
        status["Bay"] = self.bay
        status["on_job"] = self.on_job
        return status

    def log_state(self):
        self.logger.debug("STATE: " + self.state_as_string())
        self.logger.debug("on_job: " + str(self.on_job))
        if self.on_job:
            self.logger.debug("Current Job Part:\n" + str(self.whole_job[self.current_job_part]))
        self.logger.debug("bay: " + str(self.bay))

    def state_as_string(self) -> str:
        if self.state == self.STATE_IDLE: return "STATE_IDLE"
        elif self.state == self.STATE_TAKEOFF: return "STATE_TAKEOFF"
        elif self.state == self.STATE_LANDING: return "STATE_LANDING"
        elif self.state == self.STATE_IN_FLIGHT: return "STATE_IN_FLIGHT"
        elif self.state == self.STATE_IN_DELIVERY: return "STATE_IN_DELIVERY"
        elif self.state == self.STATE_IN_PICKUP: return "STATE_IN_PICKUP"