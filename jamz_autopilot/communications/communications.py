import asyncio
import json
import uuid

from .producer import KafkaProducer
from .consumer import KafkaConsumer

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaError

class Communications:

    # Kafka Bootstrap & config
    endpoints = 'confluent.loganrodie.me'
    id = hex(uuid.getnode())
    topic = "DRONE_" + id

    def __init__(self, loop, test: bool):

        self.flight_controller = None

        # Set up ready event
        self.ready = asyncio.locks.Event(loop=loop)

        # Disable automatic producing and consuming if running a unit test
        self.test = test

        # Manage the topic info. The drones topic is based on its MAC address to ensure its unique.
        self.loop = loop
        loop.create_task(self._initialize())

    # Now for the async initialization
    async def _initialize(self):

        # Admin client for topic management
        self.client = AdminClient({'bootstrap.servers': self.endpoints}, )

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
        self.loop.create_task(self.poll_commands())

    def send_status(self):
        if self.flight_controller is not None:
            status = self.flight_controller.translator.get_heartbeat_status()
            self.producer.produce(self.topic, key="status", value=json.dumps(status))
        self.loop.call_later(1, self.send_status)
        # TODO implement delivery ack logic

    async def poll_commands(self):
        message = self.consumer.poll(1)
        if message is not None:
            await self.flight_controller.push_command(json.loads(message.value().decode("ascii")))
        self.loop.create_task(self.poll_commands())

    # This is used to check if the drone's topic exists in our kafka cluster
    async def check_topic(self):
        if self.client.list_topics(self.topic).topics[self.topic].error:
            topics = self.client.create_topics(
                [NewTopic(self.topic, num_partitions=1, replication_factor=1),
                 NewTopic(self.topic + "_COMMAND", num_partitions=1, replication_factor=1)])
            try:
                for topic, future in topics.items():
                    future.result()

            except Exception as e:
                print("Failed to create a topic for {}: {}".format(self.topic, e))

    # def on_error(self, error: KafkaError):
    #     if error.code() == error.NO_ERROR:
    #         return
    #
    #     elif error.code() == error.BROKER_NOT_AVAILABLE:
    #

    def __del__(self):
        del self.client
        del self.producer
        self.consumer.close()