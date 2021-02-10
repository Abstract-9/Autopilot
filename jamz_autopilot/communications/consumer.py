from confluent_kafka import Consumer


class KafkaConsumer(Consumer):

    def __init__(self, drone_id, bootstrap_servers):
        super().__init__({
            'bootstrap_servers': bootstrap_servers,
            'client_id': drone_id,
            'auto.offset.reset': "earliest"
        })
