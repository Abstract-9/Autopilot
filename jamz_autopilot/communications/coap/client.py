import logging

from aiocoap import Message, Code, Context
import asyncio
import uuid
import json

from app import App


class Client:

    drone_id = hex(uuid.getnode())
    request_uri = "coap://<placeholder>?drone_id=" + drone_id  # TODO Figure out this ip
    log = logging.getLogger(__name__)

    def __init__(self):
        self.flight_controller = None
        self.client = None
        self.outgoing_messages = []

        # Set up ready event
        self.ready = asyncio.locks.Event()
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        self.client = await Context.create_client_context()

        # Thats all of the setup for now, lets go
        self.ready.set()
        asyncio.create_task(self.status_loop())

    async def status_loop(self):
        if self.flight_controller is not None:
            # Grab flight status
            status = self.flight_controller.translator.get_heartbeat_status()
            response = {"status": status, "messages": []}

            # Handle outgoing messages
            while len(self.outgoing_messages) > 0:
                response["messages"].append(self.outgoing_messages.pop())
            if len(response["messages"]) == 0:
                response.pop("messages")

            # Construct and send request
            message = Message(code=Code.PUT, uri=self.request_uri, payload=json.dumps(status))
            response = await self.client.request(message).response

            # Handle Response
            if response.code == Code.INTERNAL_SERVER_ERROR:
                self.log.error("Received ISR from Drone Manager...")
                pass # TODO some error handling
            elif response.code == Code.CONTENT:
                self.log.info("Received messages from Drone Manager")
                content = json.loads(response.payload)
                asyncio.run_coroutine_threadsafe(self.flight_controller.handle_messages(content.messages),
                                                 App.flight_con_event_loop)
            elif response.code != Code.VALID:
                self.log.debug("Received unknown response from drone manager: " + response.code)

            await asyncio.sleep(1)
            asyncio.create_task(self.status_loop())

    # To be called from the flight controller thread
    async def append_outgoing(self, message):
        self.outgoing_messages.append(message)

