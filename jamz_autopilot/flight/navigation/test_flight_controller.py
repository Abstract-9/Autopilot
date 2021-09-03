import asyncio

import logging

from .translation import MavLink
from .message_broker import MessageBroker
from .flight_controller import FlightController


"""
    The test flight controller is used for testing single-drone deployments. As such, we ignore all safety factors
    built in for multi-drone deployments such as landing bays, flight paths etc.
    
    This is done by faking the methods that check for approval messages from the fleet manager.
"""


class TestFlightController (FlightController):

    STATE_IN_AIR_IDLE = 6

    async def _initialize(self):
        # Wait for the mavlink connection to be active
        await self.translator.is_ready.wait()

        # Ignore landing bays and get straight to it
        asyncio.create_task(self.main_loop())

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
        elif self.state == self.STATE_IN_AIR_IDLE:
            await self.in_air_idle_actions()

    async def delivery_actions(self):
        self.current_job_part += 1
        await self.handle_next_path()
        await asyncio.sleep(1)
        if self.current_path is None:
            self.set_state(self.STATE_IN_AIR_IDLE)
        else:
            self.set_state(self.STATE_IN_FLIGHT)

    async def pickup_actions(self):
        self.current_job_part += 1
        await self.handle_next_path()
        await asyncio.sleep(1)
        if self.current_path is None:
            self.set_state(self.STATE_IN_AIR_IDLE)
        else:
            self.set_state(self.STATE_IN_FLIGHT)

    async def in_air_idle_actions(self):
        if self.on_job:
            if not self.current_path:
                await self.handle_next_path()
            else:
                self.set_state(self.STATE_IN_FLIGHT)
        else:
            job_message = await self.message_broker.get_message_by_event_type("JobAssignment")
            if job_message is not None:
                self.logger.info("Received Job ")
                self.whole_job = job_message["job_waypoints"]
                self.current_job_part = 0
                self.on_job = True

    async def get_bay_clearance(self):
        self.has_bay_clearance = True

    async def handle_next_path(self):
        # The idea here is that we don't want to go back to the landing bay when we finish our job. We just hang out
        # where we are and wait for another command.
        self.check_job_state()
        if self.on_job:
            current_job_part = self.whole_job[self.current_job_part]
            destination = \
                {"lat": current_job_part["geometry"]["lat"], "lng": current_job_part["geometry"]["lng"]}
            self.current_path = destination
