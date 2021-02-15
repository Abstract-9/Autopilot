import aiounittest
import asyncio
import random

from jamz_autopilot.communications.communications import Communications

from confluent_kafka import TopicPartition, OFFSET_END


class BasicReadWrite(aiounittest.AsyncTestCase):

    async def test_read_write(self):
        comms = Communications(asyncio.get_event_loop(), True)
        test_str = "test_" + str(random.randint(1, 100))
        comms.config["test"] = test_str

        await comms.ready.wait()

        comms.consumer.unsubscribe()
        comms.consumer.subscribe([comms.topic])
        comms.producer.produce(comms.topic, key="test", value=test_str)

        # Fast Forward in case of lag
        partition = TopicPartition(comms.topic, 0)
        partition.offset = OFFSET_END
        comms.consumer.assign([partition])

        for i in range(1, 5):
            message = comms.consumer.poll(1)
            if message is not None and message.key() is not None:
                self.assertEqual("test", message.key().decode('ascii'))
                self.assertEqual(test_str, message.value().decode('ascii'))
                break
            await asyncio.sleep(1)
            if i == 4:
                self.fail("No message seen from consumer")

