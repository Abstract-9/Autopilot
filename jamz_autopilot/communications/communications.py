import requests
import asyncio
import json
import uuid

from .producer import KafkaProducer
from .consumer import KafkaConsumer
from confluent_kafka.admin import AdminClient, NewTopic

class Communications:
    home = "http://confluent.loganrodie.me/"

    def __init__(self, loop):
        response = requests.get(self.home + "api/v1/initialize")
        data = response.json()
        # Manage the topic info. The drones topic is based on its MAC address to ensure its unique.
        self.id = hex(uuid.getnode())
        self.topic = "DRONE_" + self.id
        self.loop = loop
        self.event = CommandEvent()
        loop.call_soon(self._initialize)

    # Now for the async initialization
    async def _initialize(self):
        await self.check_topic()
        # Configuration
        self.endpoints = ['confluent.loganrodie.me:9092']

        self.producer = KafkaProducer(self.id, self.endpoints)

        self.consumer = KafkaConsumer(self.id, self.endpoints)
        self.consumer.subscribe(self.topic + "_COMMAND")

        self.client = AdminClient({'bootstrap.servers': self.endpoints})
        self.loop.call_soon(self.send_status())

    def send_status(self):
        config = {}  # Dummy variable, to be replaced with the actual config provided by core
        self.producer.produce(self.topic, key="status", value=json.dumps({
            "location": config['location'],
            "battery": config['battery'],
            "velocity": config['velocity'],
        }))
        self.loop.call_later(1, self.send_status)
        # TODO implement delivery ack logic

    def poll_commands(self):
        message = self.consumer.poll(1)
        if message is not None:
            while self.event.is_set():
                asyncio.sleep(0.5)
            self.event.command = json.loads(message.value())
            self.event.set()


    # This is used to check if the drone's topic exists in our kafka cluster
    async def check_topic(self):
        if self.topic not in self.client.list_topics(self.topic).topics:
            topic, future = await self.client.create_topics(
                [NewTopic(self.topic, num_partitions=1, replication_factor=1),
                 NewTopic(self.topic + "_COMMAND", num_partitions=1, replication_factor=1)])
    
            try:
                future.result()
            except Exception as e:
                print("Failed to create topic {}: {}".format(self.topic, e))




class CommandEvent(asyncio.Event):

    def __init__(self):
        super(CommandEvent, self).__init__()
        self.command = None