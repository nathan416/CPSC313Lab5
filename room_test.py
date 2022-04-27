""" By: Nathan Flack
    Assignment: Lab 5: Message based chat MVP3
    Class: CPSC 313- Distributed and Cloud Computing
    Due: April 24, 2022 11:59 AM

    tests for Room Chat implementation
"""
import pprint as pp
import unittest
from itertools import repeat

from constants import *
from room import *

LOGGER = logging.getLogger(__name__)

class Test_ChatRoom(unittest.TestCase):
    """Test class for ChatRoom class methods
    tests for connecting to mongodb and sending and retrieving messages
    from the database
    """
    stats_client = StatsClient(host='34.94.46.140', port=8125, prefix='cwtest')
    
    def setUp(self):
        """ initializes tests
            Set up a ChatRoom instance for both public and private rooms
        """
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, filename="room_test.log")
        self.room_list = RoomList(DEFAULT_ROOM_LIST_NAME)
        self.users = UserList(DEFAULT_USER_LIST_NAME)
        self.room_public = self.room_list.get(PUBLIC_ROOM_NAME)
        if self.room_public is None:
            self.room_public = self.room_list.create(room_name=PUBLIC_ROOM_NAME, owner_alias=USER_ALIAS, member_list=[USER_ALIAS, 'eshner'], room_type=ROOM_TYPE_PUBLIC)
        
        self.room_private = self.room_list.get(PRIVATE_ROOM_NAME)
        if self.room_private is None:
            self.room_private = self.room_list.create(room_name=PRIVATE_ROOM_NAME, owner_alias=USER_ALIAS, member_list=[USER_ALIAS, 'eshner'], room_type=ROOM_TYPE_PRIVATE)
        self.__last_private_message_sent: str = ''
        self.__last_public_message_sent: str = '' 
        self.stats_client.incr('room_test_count')
        

    def test_get_messages(self):
        """ test getting 20 messages
        """
        LOGGER.debug("entering test_get_messages")
        message_list, message_objects, num_messages = self.room_public.get_messages(USER_ALIAS, 20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))

    def test_send_message(self):
        """test sending one basic message
        """
        LOGGER.debug("entering test_send_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE}\''))

    def test_send_empty_message(self):
        """test sending one empty message
        """
        LOGGER.debug("entering test_send_empty_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_EMPTY, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_EMPTY}\''))

    def test_send_short_message(self):
        """test sending one short message
        """
        LOGGER.debug("entering test_send_short_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_SHORT, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_SHORT}\''))

    def test_send_long_message(self):
        """test sending one long message
        """
        LOGGER.debug("entering test_send_long_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_LONG, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_LONG}\''))

    def test_send_number_message(self):
        """test sending one number message
        """
        LOGGER.debug("entering test_send_number_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_NUMBERS, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_NUMBERS}\''))

    def test_send_receive_message(self):
        """test sending and receiving a message
        """
        LOGGER.debug("entering test_send_receive_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE, USER_ALIAS))
        message_list, message_objects, num_messages = self.room_public.get_messages(USER_ALIAS, 20, False)
        self.assertIsNot(message_list, [])

        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE, message_list)

    def test_send_receive_multiple_messages(self):
        """test sending and receiving 10 messages
        """
        LOGGER.debug('entering test_send_receive_multiple_messages')
        for loop_control in range(0, 10):
            self.assertTrue(
                self.room_public.send_message(TEST_MESSAGE, USER_ALIAS)
            )
        message_list, message_objects, num_messages = self.room_public.get_messages(USER_ALIAS, 1000, False)
        self.assertIsNot(message_list, [])

        LOGGER.debug(pp.pformat(message_list))
        self.assertTrue(set(repeat(TEST_MESSAGE, 10)).issubset(message_list))

    def test_send_receive_empty_message(self):
        """test sending one empty message
        """
        LOGGER.debug("entering test_send_empty_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_EMPTY, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_EMPTY}\''))
        message_list, message_objects, num_messages = self.room_public.get_messages(USER_ALIAS, 20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_EMPTY, message_list)

    def test_send_receive_short_message(self):
        """test sending one short message
        """
        LOGGER.debug("entering test_send_short_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_SHORT, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_SHORT}\''))
        message_list, message_objects, num_messages = self.room_public.get_messages(USER_ALIAS, 20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_SHORT, message_list)

    def test_send_receive_long_message(self):
        """test sending one long message
        """
        LOGGER.debug("entering test_send_long_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_LONG, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_LONG}\''))
        message_list, message_objects, num_messages = self.room_public.get_messages(USER_ALIAS, 20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_LONG, message_list)

    def test_send_receive_number_message(self):
        """test sending one number message
        """
        LOGGER.debug("entering test_send_number_message")

        self.assertTrue(self.room_public.send_message(TEST_MESSAGE_NUMBERS, USER_ALIAS))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_NUMBERS}\''))
        message_list, message_objects, num_messages = self.room_public.get_messages(USER_ALIAS, 20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_NUMBERS, message_list)

    def test_room_list_add(self):
        chat_room = ChatRoom(PUBLIC_ROOM_NAME, [], USER_ALIAS, USER_ALIAS, True)
        self.room_list.add(chat_room)
        
    
    def test_send(self):
        """ create the messages to send, send them and assert that the call returned success
            Keep track of messages sent to compare in the full test
        """
        private_message = TEST_MESSAGE
        public_message = TEST_MESSAGE2
        if (first_user := self.users.get('eshner')) is None:
            self.users.register('eshner')
        if (second_user := self.users.get('testing')) is None:
            second_user = self.users.register('testing')
        self.users.persist()
        self.room_public.add_member(first_user.alias)
        self.room_public.add_member(second_user.alias)
        self.room_private.add_member(first_user.alias)
        self.room_private.add_member(second_user.alias)
        sent_messages = list()
        cur_time = datetime.now()
        private_message += f'{str(datetime.date(cur_time))}-{str(datetime.time(cur_time))} '
        public_message += f'{str(datetime.date(cur_time))}-{str(datetime.time(cur_time))} '
        try:
            self.assertEqual(self.room_private.send_message(message=private_message, from_alias=USER_ALIAS), True)
            self.__last_private_message_sent = private_message
            sent_messages.append(private_message)
            self.assertEqual(self.room_public.send_message(message=public_message, from_alias=USER_ALIAS), True)
            self.__last_public_message_sent = public_message
            sent_messages.append(public_message)
            return sent_messages
        except AssertionError as problem:
            LOGGER.warning(f'SEND ERROR::Assertions failed in send_test: {problem}')
            return None

    def test_get(self):
        """ Get messages, assert that we got what we expect
            Keep track of both public and private messages and return either private only or both depending on flag

        """
        private_only = False
        try:
            if (first_user := self.users.get('eshner')) is None:
                self.users.register('eshner')
            if (second_user := self.users.get('testing')) is None:
                second_user = self.users.register('testing')
            self.users.persist()
            self.room_public.add_member(first_user.alias)
            self.room_public.add_member(second_user.alias)
            self.room_private.add_member(first_user.alias)
            self.room_private.add_member(second_user.alias)
            private_messages, private_objects, total_private_messages = self.room_private.get_messages(user_alias=USER_ALIAS, return_objects=True)
            self.assertEqual(len(private_messages), total_private_messages)
            LOGGER.debug(f'Private message get is fine. Number: {total_private_messages}, messages: {private_messages}')
            if private_only is True:
                return private_messages, private_objects, total_private_messages
            public_messages, public_objects, total_public_messages = self.room_public.get_messages(user_alias=USER_ALIAS, return_objects=True)
            self.assertEqual(len(public_messages), total_public_messages)
            LOGGER.debug(f'Public message get is fine. Number: {total_public_messages}, messages: {public_messages}')
            text_messages = list()
            text_messages = private_messages + public_messages
            text_objects = private_objects + public_objects
            total_messages = total_private_messages + total_public_messages
            self.assertEqual(total_messages, len(text_messages))
            LOGGER.debug(f'Total message get is fine. Number: {total_messages}, messages: {text_messages}')
            return text_messages
        except AssertionError as problem:
            LOGGER.warning(f'GET ERROR::Assertions failed in get_test. Error: {problem}')
            return None

    def test_full(self):
        """ Mostly calling the send and get methods and comparing what we actually got against what we sent
        """
        try:
            send_result = self.test_send()
            print(f'Inside full test for room, send_result is: {send_result}')
            self.assertIsNotNone(send_result)
        except AssertionError as problem:
            print(f"SEND ERROR:: inside FULL test. Problem is {problem}")
        try:
            get_result = self.test_get()
            print(f'Inside full test for room, get_result is: {get_result}')
            self.assertIsNotNone(get_result)
        except AssertionError as problem:
            print(f'GET ERROR:: Inside FULL test. Problem is {problem}')
        try:
            if send_result is not None:
                for sent_message in send_result:
                    print(f'Inside full RMQ test looping sent messages. Cur message is {sent_message}')
                    self.assertIn(sent_message, get_result)
        except AssertionError as problem:
            print(f'E2E ERROR:: Inside FULL test. Problem is {problem}')


if __name__ == "__main__":
    unittest.main()
