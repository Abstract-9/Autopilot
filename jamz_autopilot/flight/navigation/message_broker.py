import asyncio
import json

class MessageBroker:
    
    def __init__(self):
        from app import App

        self.incoming_messages = []
        self.waiting_on_bay_access = False
        self.waiting_on_path_proposal = False
        self.bay_cleared = False
        
        self.outgoing_messages_lock = asyncio.Lock()
        self.incoming_messages_lock = asyncio.Lock()
    
    # Message format:
    # {
    #   "eventType": EventType,
    #   "payload": EventData
    # }
    async def handle_messages(self, messages):
        await self.incoming_messages_lock.acquire()
        for message in messages:
            # Newest messages go on the back, messages get consumed from the front
            self.incoming_messages.append(message)
        self.incoming_messages_lock.release()
    
    async def send_message(self, message):
        # Deal With internal states
        if message["eventType"] == "AccessRequest":
            self.waiting_on_bay_access = True
            self.bay_cleared = False
        elif message["eventType"] == "PathProposal":
            self.waiting_on_path_proposal = True
        # Send out message
        asyncio.create_task(App.comms.append_outgoing(message))
        
    async def get_message_by_event_type(self, event_type) -> dict:
        await self.incoming_messages_lock.acquire()
        for i in range(len(self.incoming_messages)):
            message = self.incoming_messages[i]
            if message["eventType"] == event_type:

                # Deal with internal states
                if message["eventType"] == "AccessGranted":
                    self.waiting_on_bay_access = False
                elif message["eventType"] == "PathAssignment":
                    self.waiting_on_path_proposal = False

                # Return Message
                self.incoming_messages_lock.release()
                return self.incoming_messages.pop(i)

        self.incoming_messages_lock.release()
        return {}

    async def ensure_bay_cleared(self):
        if not self.bay_cleared:
            await self.send_message(self.generate_bay_cleared())
            self.bay_cleared = True

    @staticmethod
    def generate_access_request(bay_id):
        return json.dumps({"eventType": "AccessRequest", "bay_id": bay_id})
    
    @staticmethod
    def generate_path_proposal(start, end):
        return json.dumps({"eventType": "PathProposal", "start": start, "end": end})

    @staticmethod
    def generate_bay_cleared():
        return json.dumps({"eventType": "AccessComplete"})