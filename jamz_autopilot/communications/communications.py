import requests
import asyncio
import json
import uuid

from .producer import KafkaProducer
from confluent_kafka.admin import AdminClient, NewTopic

class Communications:
    home = "http://confluent.loganrodie.me/"

    def __init__(self, loop):
        response = requests.get(self.home + "api/v1/initialize")
        data = response.json()
        # Manage the topic info. The drones topic is based on its MAC address to ensure its unique.
        self.topic = "DRONE_" + hex(uuid.getnode())
        self.topic_confirmed = False
        # Configuration
        self.endpoints = ['confluent.loganrodie.me:9092']
        self.producer = KafkaProducer(hex(uuid.getnode()), self.endpoints)
        self.client = AdminClient({'bootstrap.servers': self.endpoints})
        self.loop = loop
        self.send_status()

    def send_status(self):
        config = {}  # Dummy variable, to be replaced with the actual config provided by core
        if self.topic_confirmed:
            self.producer.produce(self.topic, key="status", value=json.dumps({
                "location": config['location'],
                "battery": config['battery'],
                "velocity": config['velocity'],
            }))
        else:
            self.check_topic()
        self.loop.call_later(1, self.send_status)
        # TODO implement delivery ack logic

    # This is called if the drone's topic doesn't exist in our kafka cluster
    async def check_topic(self):
        if self.topic in self.client.list_topics(self.topic).topics:
            self.topic_confirmed = True
        else:
            topic, future = await self.client.create_topics(
                [NewTopic(self.topic, num_partitions=1, replication_factor=1)])
    
            try:
                future.result()
            except Exception as e:
                print("Failed to create topic {}: {}".format(self.topic, e))




class CommandEvent(asyncio.Event):
    TYPE_COMMAND = 0
    coords = []


    def __init__(self, type):
        super(CommandEvent, self).__init__()
        self.type = type