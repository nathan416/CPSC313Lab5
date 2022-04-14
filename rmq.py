"""By: Nathan Flack
Assignment: Lab 3: Message based cha
Class: CPSC 313- Distributed and Cloud Computing
Due: February 20, 2022 11:59 AM

RabbitMessageQ implementation using pika to interact with rabbitmq server
"""
import pika
import logging
from pika.exchange_type import ExchangeType
import pprint as pp

LOGGER = logging.getLogger(__name__)
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -43s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')


class RabbitMessageQ:
    """Class to interact with a rabbit message queue. 
    """
    EXCHANGE = 'general'
    EXCHANGE_TYPE = ExchangeType.fanout
    PUBLISH_INTERVAL = 1
    PRIVATE_QUEUE = 'nathan_private'
    PRIVATE_ROUTING_KEY = 'nathan-private-key'

    def __init__(self, amqp_url):
        """Setup the RabbitMessageQ object, passing in the URL we will use
        to connect to RabbitMQ.
        :param str amqp_url: The URL for connecting to RabbitMQ, 
        url is in the form 'amqp://{USERNAME}:{PASSWORD}@{DNS}:{PORT}
        an example: 'amqp://username:password@example.com:5672'
        """
        self._message_number = None
        self._received_messages = []

        self._stopping = False
        self._url = amqp_url
        self._prefetch_count = 0

        self._connection = pika.BlockingConnection(
            pika.URLParameters(self._url))
        self._channel = self._connection.channel()

        self._channel.exchange_declare(exchange=self.EXCHANGE,
                                       exchange_type=self.EXCHANGE_TYPE,
                                       passive=False,
                                       auto_delete=False)

    def get_received_messages(self):
        """returns list of message bodies from the self._received_messages private variable

        Returns:
            list: list of messages
        """
        return_messages = []
        for messages in self._received_messages:
            return_messages.append(messages[2])
        return return_messages

    def send_message(self, message: str):
        """send a message to all queues binded to the general exchange

        Args:
            message (str): message to send to the queue
        """
        LOGGER.info(f'Starting send_message')
        if self._channel is None or not self._channel.is_open:
            return

        self._channel.queue_declare(self.PRIVATE_QUEUE)
        self._channel.queue_bind(
            self.PRIVATE_QUEUE, self.EXCHANGE, routing_key=self.PRIVATE_ROUTING_KEY)
        self._channel.basic_qos(prefetch_count=self._prefetch_count)

        properties = pika.BasicProperties(
            app_id='nathan-publisher',
            content_type='application/json')
        self._message_number = 1

        self._channel.confirm_delivery()
        try:
            self._channel.basic_publish(self.EXCHANGE, self.PRIVATE_ROUTING_KEY,
                                        message,
                                        properties)
            LOGGER.info('Published message # %i, message= \"%s\"',
                        self._message_number, message)
        except pika.exceptions.UnroutableError as exception:
            LOGGER.error(exception.message)

    def consume_message(self, message_amount: int):
        """consume the messages in the queue, adds it to the received_messages class variables, return a list of the messages

        Args:
            message_amount (int): max amount of messages to consume before stopping

        Returns:
            list: list of consumed messages
        """
        self._channel.queue_declare(
            queue=self.PRIVATE_QUEUE, auto_delete=False)
        self._channel.queue_bind(
            queue=self.PRIVATE_QUEUE, exchange=self.EXCHANGE, routing_key=self.PRIVATE_ROUTING_KEY)
        self._channel.basic_qos(prefetch_count=self._prefetch_count)
        return_list = []

        for method, properties, body in self._channel.consume(self.PRIVATE_QUEUE, auto_ack=True, inactivity_timeout=2):
            if method is None:
                LOGGER.info(f'inactivity timeout')
                break
            formatted_body = str(body.decode('utf-8'))
            LOGGER.info(f'messages recieved: {formatted_body}')
            self._received_messages.append(
                (method, properties, formatted_body))
            return_list.append(formatted_body)
            if method.delivery_tag == message_amount:
                break
        self._channel.cancel()
        return return_list

    def acknowledge_messages(self):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.
        """
        LOGGER.info('Acknowledging messages')
        self._channel.basic_ack()

    def stop(self):
        """Stop the class by closing the channel and connection.
        """
        LOGGER.info('Stopping')
        self._stopping = True
        self.close_channel()
        self.close_connection()

    def close_channel(self):
        """Invoke this command to close the channel with RabbitMQ by sending
        the Channel.Close RPC command.
        """
        if self._channel is not None:
            LOGGER.info('Closing the channel')
            self._channel.close()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        if self._connection is not None:
            LOGGER.info('Closing connection')
            self._connection.close()


def main():
    pass


if __name__ == '__main__':
    main()
