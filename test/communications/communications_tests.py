from unittest import IsolatedAsyncioTestCase, TestCase
import uuid
import asyncio
import json
import random

from confluent_kafka import TopicPartition, OFFSET_END

from jamz_autopilot.communications.communications import Communications, KafkaConsumer, KafkaProducer, CommandEvent


class CommunicationsTest(IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.comms = Communications(asyncio.get_event_loop(), True)

        for i in range(5):
            if self.comms.ready.is_set():
                break
            elif i == 4:
                self.fail("Communications was not ready in 5 seconds.")
            else:
                await asyncio.sleep(1)

    def tearDown(self) -> None:
        del self.comms


class ConstructorTest(CommunicationsTest):

    async def test_constructor(self):
        self.assertEqual(hex(uuid.getnode()), self.comms.id)
        self.assertEqual("DRONE_" + hex(uuid.getnode()), self.comms.topic)
        self.assertIsInstance(self.comms.consumer, KafkaConsumer)
        self.assertIsInstance(self.comms.producer, KafkaProducer)
        self.assertEqual("DRONE_" + hex(uuid.getnode()) + "_COMMAND",
                         self.comms.consumer.committed([TopicPartition(self.comms.topic + "_COMMAND", 0)])[0].topic)


class CheckTopicTest (CommunicationsTest):

    async def test_check_topic(self):
        await self.comms.check_topic()

        # Ensure the topics exist
        topic = self.comms.client.list_topics(self.comms.topic)
        self.assertIsNone(topic.topics[self.comms.topic].error)
        topic = self.comms.client.list_topics(self.comms.topic + "_COMMAND")
        self.assertIsNone(topic.topics[self.comms.topic + "_COMMAND"].error)


class SendStatusTest (CommunicationsTest):

    async def test_send_status(self):
        self.comms.config = {
            'lat': 'test_lat',
            'lon': 'test_lon',
            'alt': 'test_alt',
            'battery': 'test_' + str(random.randint(1, 100))
        }

        self.comms.consumer.unsubscribe()
        self.comms.consumer.subscribe([self.comms.topic])

        # Fast Forward in case of lag
        partition = TopicPartition(self.comms.topic, 0)
        partition.offset = OFFSET_END
        self.comms.consumer.assign([partition])

        self.comms.send_status()

        for i in range(1, 5):
            message = self.comms.consumer.poll(1)
            if message is not None and message.key() is not None:
                self.assertEqual("status", message.key().decode('ascii'))
                self.assertEqual(self.comms.config, json.loads(message.value().decode('ascii')))
                break
            # If we didn't see the message, we probably fast-forwarded too early. Lets try again
            self.comms.send_status()
            await asyncio.sleep(1)
            if i == 4:
                self.fail("No message seen from consumer")


class PollCommandsTest (CommunicationsTest):

    async def test_poll_commands(self):
        test_str = 'test' + str(random.randint(1, 100))
        self.comms.producer.produce(self.comms.topic + "_COMMAND", json.dumps({'test': test_str}))

        await self.comms.event.wait()

        self.assertEqual(test_str, self.comms.event.command['test'])

class CommandEventTest (IsolatedAsyncioTestCase):

    async def test_command_event(self):
        test_command = json.dumps({'test123': 'test1234'})
        event = CommandEvent()
        event.command = test_command
        event.set()

        await event.wait()

        self.assertEqual(test_command, event.command)
