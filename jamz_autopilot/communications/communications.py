import asyncio
import json
import uuid

from .producer import KafkaProducer
from .consumer import KafkaConsumer
from ..core import Core

from confluent_kafka.admin import AdminClient, NewTopic


class Communications:
    config = Core.get_instance().config
    ready = asyncio.locks.Event()

    # Kafka Bootstrap & config
    endpoints = 'confluent.loganrodie.me'
    id = hex(uuid.getnode())
    topic = "DRONE_" + id

    def __init__(self, loop, test: bool):
        # Disable automatic producing and consuming if running a unit test
        self.test = test

        # Manage the topic info. The drones topic is based on its MAC address to ensure its unique.
        self.loop = loop
        self.event = CommandEvent()
        Core.get_instance().on_comms_event(self.event)
        loop.create_task(self._initialize())

    # Now for the async initialization
    async def _initialize(self):

        # Admin client for topic management
        self.client = AdminClient({'bootstrap.servers': self.endpoints})

        # Set up topic
        await self.check_topic()

        # Configuration

        self.producer = KafkaProducer(self.id, self.endpoints)

        self.consumer = KafkaConsumer(self.id, self.endpoints)
        self.consumer.subscribe([self.topic + "_COMMAND"])

        # Ready to go!
        self.ready.set()

        if not self.test:
            self.loop.call_soon(self.send_status)

    def send_status(self):
        config = self.config
        self.producer.produce(self.topic, key="status", value=json.dumps({
            "location": config['location'],
            "battery": config['battery'],
        }))
        self.loop.call_later(1, self.send_status)
        # TODO implement delivery ack logic

    def poll_commands(self):
        message = self.consumer.poll(1)
        if message is not None:
            while self.event.is_set():
                asyncio.sleep(0.5)
            self.event.command = json.loads(message.value().decode("ascii"))
            self.event.set()
        self.loop.call_soon(self.poll_commands)

    # This is used to check if the drone's topic exists in our kafka cluster
    async def check_topic(self):
        if self.topic not in self.client.list_topics(self.topic).topics:
    
            try:
                topics = await self.client.create_topics(
                    [NewTopic(self.topic, num_partitions=1, replication_factor=1),
                     NewTopic(self.topic + "_COMMAND", num_partitions=1, replication_factor=1)])
            except Exception as e:
                print("Failed to create a topic for {}: {}".format(self.topic, e))


class CommandEvent(asyncio.Event):

    def __init__(self):
        super(CommandEvent, self).__init__()
        self.command = None
