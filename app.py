import asyncio
import configparser
import os

from jamz_autopilot.communications import Client
from jamz_autopilot.flight.navigation import FlightController, TestFlightController

import logging


class App:

    comms = None
    flight_con = None

    def __init__(self):
        logging.basicConfig(level=logging.INFO)

        # Load the configuration
        self.load_config()

        self.comms = Client(self)

        # If testing mode is set, use the test flight controller.
        if self.config.get("Application", "Mode").lower() == "test":
            self.flight_con = TestFlightController(self)
        else:
            self.flight_con = FlightController(self)

        self.comms.message_broker = self.flight_con.message_broker
        # try:
        #     while(1):
        #         loop.run_until_complete(core.onFlightEvent())
        #         loop.run_until_complete(core.onCommsEvent())
        #     Communications(loop)
        #     Flight(loop)
        # finally:
        #     loop.close()

    def load_config(self) -> None:
        config = configparser.ConfigParser()
        # The following declares default values for the config. Values can be customized in config.ini.
        config.read_dict({
            "Application": {
                "Mode": "production",
                "Server": "192.168.0.249"
            },
            "Flight": {
                "GroundSpeed": 10
            }
        })
        config.read(os.path.join(os.getcwd(), "../config.ini"))  # Read user values from the config file
        self.config = config


async def _main():
    App()

# Python 3.7+, only run if this is the main interpreter
if __name__ == "__main__":
    asyncio.ensure_future(_main())
    asyncio.get_event_loop().run_forever()
