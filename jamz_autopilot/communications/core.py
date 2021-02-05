import requests
import asyncio
import json

from .producer import KafkaProducer

class Communications:
    home = "http://confluent.loganrodie.me/"

    def __init__(self, loop):
        response = requests.get(self.home + "api/v1/initialize")
        data = response.json()
        self.topic = data['kafka_topic']
        self.endpoints = data['kafka_bootstrap']
        self.drone_id = data['drone_id']
        self.producer = KafkaProducer(self.drone_id, self.endpoints)
        self.loop = loop
        self.send_heartbeat()


    def send_status(self):
        config = {} # Stub variable, to be replaced with actual config class
        self.producer.produce(self.topic, key="status", value=json.dumps({
            "location": config['location'],
            "battery": config['battery'],
            "velocity": config['velocity'],
        }))
        self.loop.call_later(1, self.send_status)
        # TODO implement delivery ack logic

    def send_heartbeat(self):
        response = requests.post(self.home + "api/v1/heartbeat", json={
            "drone_id": self.drone_id,
            "status": "ok"
        })
        self.loop.call_later(10, self.send_heartbeat)
        # TODO implement delivery ack logic


class CommunicationEvent(asyncio.Event):
    TYPE_COMMAND = 0
    TYPE_HEARTBEAT = 1