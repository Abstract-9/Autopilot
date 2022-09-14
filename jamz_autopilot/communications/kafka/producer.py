from confluent_kafka import Producer


# TODO Jonathan Unit tests
class KafkaProducer(Producer):

    # TODO: Create unit test
    def __init__(self, bootstrap_servers):
        super().__init__({
            'bootstrap.servers': bootstrap_servers,
            'client.id': '1',
            'broker.address.family': 'v4',
            'broker.address.ttl': 1
        })