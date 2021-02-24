from aiounittest import AsyncTestCase
import uuid
import asyncio

from jamz_autopilot.communications.communications import Communications, KafkaConsumer, KafkaProducer

class CommunicationsTests(AsyncTestCase):

    async def test_constructor(self):
        comms = Communications(asyncio.get_event_loop(), False)

        for i in range(5):
            if comms.ready.is_set():
                break
            elif i == 4:
                self.fail("Communications was not ready in 5 seconds.")
            else:
                await asyncio.sleep(1)

        self.assertEqual(hex(uuid.getnode()), comms.id)
        self.assertEqual("DRONE_" + hex(uuid.getnode()), comms.topic)
        self.assertIsInstance(KafkaConsumer, comms.consumer)
        self.assertIsInstance(KafkaProducer, comms.producer)
        self.assertEqual("DRONE_" + hex(uuid.getnode()) + "_COMMAND", comms.consumer.committed()[0].topic)

