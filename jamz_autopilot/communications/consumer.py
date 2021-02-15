from confluent_kafka import Consumer


class KafkaConsumer(Consumer):

    def __init__(self, drone_id, bootstrap_servers):
        super().__init__({
            'bootstrap.servers': bootstrap_servers,
            'client.id': '1',
            'group.id': "DRONE",
            'broker.address.family': 'v4',
            'broker.address.ttl': 1
        })
