import asyncio
import json
import logging

from typing import Union

class MessageBroker:

    log = logging.getLogger(__name__)
    
    def __init__(self, app):

        self.incoming_messages = []
        self.waiting_on_bay_access = False
        self.waiting_on_path_proposal = False
        self.waiting_on_bay_assignment = False
        self.bay_cleared = False
        
        self.outgoing_messages_lock = asyncio.Lock()
        self.incoming_messages_lock = asyncio.Lock()

        self.app = app
    
    # Message format:
    # {
    #   "eventType": EventType,
    #   ...EventData
    # }
    async def handle_messages(self, messages):
        await self.incoming_messages_lock.acquire()
        for message in messages:
            # Newest messages go on the back, messages get consumed from the front
            self.incoming_messages.append(message)
            self.log.info("Received messages from Drone Manager: " + message["eventType"])
        self.incoming_messages_lock.release()
    
    async def send_message(self, message):
        asyncio.create_task(self.app.comms.append_outgoing(message))
        
    async def get_message_by_event_type(self, event_type) -> Union[dict, None]:
        await self.incoming_messages_lock.acquire()
        for i in range(len(self.incoming_messages)):
            message = self.incoming_messages[i]
            if message["eventType"] == event_type:

                # Deal with internal states
                if message["eventType"] == "AccessGranted":
                    self.waiting_on_bay_access = False
                elif message["eventType"] == "PathAssignment":
                    self.waiting_on_path_proposal = False
                elif message["eventType"] == "BayAssignment":
                    self.waiting_on_bay_assignment = False

                # Return Message
                self.incoming_messages_lock.release()
                return self.incoming_messages.pop(i)

        self.incoming_messages_lock.release()
        return None

    async def ensure_bay_cleared(self):
        if not self.bay_cleared:
            await self.send_message(self.generate_bay_cleared())
            self.bay_cleared = True

    def generate_access_request(self, bay_id) -> dict:
        self.waiting_on_bay_access = True
        return {"eventType": "AccessRequest", "bay_id": bay_id}

    def generate_path_proposal(self, start, end) -> dict:
        self.waiting_on_path_proposal = True
        return {"eventType": "PathProposal", "start": start, "end": end}

    def generate_assignment_request(self, location: dict) -> dict:
        self.waiting_on_bay_assignment = True
        return {"eventType": "AssignmentRequest", "geometry": location}

    @staticmethod
    def generate_bay_cleared() -> dict:
        return {"eventType": "AccessComplete"}