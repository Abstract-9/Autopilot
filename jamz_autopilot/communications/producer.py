from confluent_kafka import Producer

class KafkaProducer(Producer):

    def __init__(self, drone_id, bootstrap_servers):
        super().__init__({
            'bootstrap.servers': bootstrap_servers,
            'client.id': '1',
            'broker.address.family': 'v4',
            'broker.address.ttl': 1
        })