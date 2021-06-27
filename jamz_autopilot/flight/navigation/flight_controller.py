import asyncio

import logging

from .translation import Ardupilot
from .flight_event import FlightEvent
from .message_broker import MessageBroker

# Controller holds instance of link interface
# Controller manages all flight variables and pass commands to
# link interface- in link interface we interact with dronekit
# Controller uses option lock to make one flight command go at a time
# use lock to make sure only one command happening at time


class FlightController:

    # How to connect to the hardware flight controller. Some examples;
    # "/dev/ttyACM0" Serial interface over USB
    # "tcp:127.0.0.1:6603" Local TCP connection
    # "udp:127.0.0.1:5202" Local UDP connection
    device = "tcp:localhost:5760"

    logger = logging.getLogger(__name__)

    # Some constants for state management

    STATE_IDLE = 0
    STATE_TAKEOFF = 1
    STATE_LANDING = 2
    STATE_IN_FLIGHT = 3
    STATE_IN_PICKUP = 4
    STATE_IN_DELIVERY = 5

    def __init__(self, device=None):

        # Variables for flight management
        self.state = self.STATE_IDLE
        self.has_bay_clearance = False
        self.has_path_clearance = False
        self.on_job = False
        self.whole_job = None
        self.current_job_part = None
        self.bay_id = None
        self.destination = None
        self.current_path = None

        # Use custom connection string if supplied
        if device:
            self.device = device

        # Initialize synchronization primitives
        self.commands_lock = asyncio.Lock()
        self.operation_lock = asyncio.Lock()

        # Initialize hardware translator
        self.translator = Ardupilot(self.device)

        # Message Broker
        self.message_broker = MessageBroker()

        asyncio.create_task(self.main_loop())

    # Genuinely, the thick of the logic.
    # Handle how to fly. Designed as a state machine, with decision trees under each state.
    async def main_loop(self):
        if self.state == self.STATE_IDLE:
            # IDLE + on_job = waiting to take off
            if self.on_job:
                if not self.current_path:
                    await self.get_path_clearance()
                else:
                    if not self.has_bay_clearance:
                        bay_clearance_granted = await self.message_broker.get_message_by_event_type("AccessGranted")
                        if bay_clearance_granted == {} and not self.message_broker.waiting_on_bay_access:
                            await self.message_broker.send_message(
                                self.message_broker.generate_access_request(self.bay_id))
                        elif bay_clearance_granted != {}:
                            self.set_state(self.STATE_TAKEOFF)
                            self.has_bay_clearance = True
            else:
                job_message = await self.message_broker.get_message_by_event_type("JobAssignment")
                if job_message is not None:
                    self.whole_job = job_message["payload"]["job_waypoints"]
                    self.current_job_part = 0
                    self.on_job = True

        elif self.state == self.STATE_TAKEOFF:
            if self.has_bay_clearance:
                if self.translator.status == self.translator.STATUS_EXECUTING_COMMAND:
                    status = await self.translator.ensure_ascend()
                    if status == self.translator.STATUS_DONE_COMMAND:
                        self.translator.status = self.translator.STATUS_IDLE
                        self.set_state(self.STATE_IN_FLIGHT)
                        self.has_bay_clearance = False
                    elif status > 20:
                        await self.message_broker.ensure_bay_cleared()
                elif self.translator.status == self.translator.STATUS_IDLE:
                    await self.translator.ascend(self.current_path["altitude"])
        elif self.state == self.STATE_LANDING:
            pass
        elif self.state == self.STATE_IN_FLIGHT:
            if self.translator.status == self.translator.STATUS_IDLE:
                await self.translator.goto(self.current_path.start)
            if self.translator.status == self.translator.STATUS_EXECUTING_COMMAND:
                status = await self.translator.ensure_goto()
                if status == self.translator.STATUS_DONE_COMMAND:
                    self.current_path = None
                    part_type = self.whole_job[self.current_job_part]["type"]
                    if part_type == "delivery":
                        self.set_state(self.STATE_IN_DELIVERY)
                    else:
                        self.set_state(self.STATE_IN_PICKUP)

        elif self.state == self.STATE_IN_DELIVERY:
            self.current_job_part += 1
            await self.get_path_clearance()
            await asyncio.sleep(5)
            while self.current_path is None:
                await asyncio.sleep(5)
            self.set_state(self.STATE_IN_FLIGHT)
        elif self.state == self.STATE_IN_PICKUP:
            self.current_job_part += 1
            await self.get_path_clearance()
            await asyncio.sleep(5)
            while self.current_path is None:
                await asyncio.sleep(5)
            self.set_state(self.STATE_IN_FLIGHT)

        self.log_state()
        # Schedule callback
        await asyncio.sleep(0.5)
        asyncio.create_task(self.main_loop())

    # Super important, call this method before setting sub-states!
    def set_state(self, state):
        # Reset state-dependent booleans (sub_states)
        self.has_bay_clearance = False
        self.bay_id = None
        self.destination = None
        self.waiting_on_response = None

        # Set the state
        self.state = state

    async def handle_delivery(self):
        # TODO
        pass

    async def handle_pickup(self):
        # TODO
        pass

    async def get_path_clearance(self):
        path_assignment = await self.message_broker.get_message_by_event_type("PathAssignment")
        if path_assignment == {} and not self.message_broker.waiting_on_path_proposal:
            location = self.translator.get_location()
            current_job_part = self.whole_job[self.current_job_part]
            path_proposal = self.message_broker.generate_path_proposal(
                {location["latitude"], location["longitude"]},
                {current_job_part["geometry"]["latitude"], current_job_part["geometry"]["longitude"]}
            )
            await self.message_broker.send_message(path_proposal)
        elif path_assignment != {}:
            self.current_path = path_assignment["payload"]

    def log_state(self):
        self.logger.info("STATE: " + self.state_as_string())
        self.logger.info("on_job: " + str(self.on_job))
        if self.on_job:
            self.logger.info("Current Job Part:\n" + str(self.whole_job[self.current_job_part]))
        self.logger.info("bay_id: " + str(self.bay_id))
        self.logger.info("")

    def state_as_string(self) -> str:
        if self.state == self.STATE_IDLE: return "STATE_IDLE"
        elif self.state == self.STATE_TAKEOFF: return "STATE_TAKEOFF"
        elif self.state == self.STATE_LANDING: return "STATE_LANDING"
        elif self.state == self.STATE_IN_FLIGHT: return "STATE_IN_FLIGHT"
        elif self.state == self.STATE_IN_DELIVERY: return "STATE_IN_DELIVERY"
        elif self.state == self.STATE_IN_PICKUP: return "STATE_IN_PICKUP"