from confluent_kafka import Producer

class KafkaProducer(Producer):

    def __init__(self, drone_id, bootstrap_servers):
        super().__init__({
            'bootstrap_servers': bootstrap_servers,
            'client_id': drone_id
        })