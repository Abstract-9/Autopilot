import logging

from aiocoap import Message, Code, Context
import asyncio
import uuid
import json


class Client:

    drone_id = hex(uuid.getnode())
    request_uri = "coap://172.27.240.1:5683/status?drone_id=" + drone_id  # Localhost for testing
    log = logging.getLogger(__name__)

    def __init__(self, app):

        self.flight_controller = None
        self.client = None
        self.outgoing_messages = []

        self.app = app

        # Set up ready event
        self.ready = asyncio.locks.Event()
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        self.client = await Context.create_client_context()

        # Thats all of the setup for now, lets go
        while self.app.flight_con is None:
            await asyncio.sleep(1)
        self.ready.set()
        asyncio.create_task(self.status_loop())

    async def status_loop(self):
        # Grab flight status
        status = self.app.flight_con.get_transmittable_status()
        request = {"status": status, "messages": []}

        # Handle outgoing messages
        while len(self.outgoing_messages) > 0:
            request["messages"].append(self.outgoing_messages.pop())
        if len(request["messages"]) == 0:
            request.pop("messages")

        # Construct and send request
        message = Message(code=Code.PUT, uri=self.request_uri, payload=json.dumps(request).encode("ASCII"))
        response = await self.client.request(message).response

        # Handle Response
        if response.code == Code.INTERNAL_SERVER_ERROR:
            self.log.error("Received ISR from Drone Manager...")
            pass # TODO some error handling
        elif response.code == Code.CONTENT:
            self.log.info("Received messages from Drone Manager")
            content = json.loads(response.payload)
            asyncio.create_task(self.flight_controller.handle_messages(content.messages))
        elif response.code != Code.VALID:
            self.log.debug("Received unknown response from Drone Manager: " + response.code)

        await asyncio.sleep(1)
        asyncio.create_task(self.status_loop())

    # To be called from the flight controller thread
    async def append_outgoing(self, message):
        self.outgoing_messages.append(message)

