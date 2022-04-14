""" By: Nathan Flack
    Assignment: Lab 4: Message based chat MVP2
    Class: CPSC 313- Distributed and Cloud Computing
    Due: March 20, 2022 11:59 AM

    tests for Room Chat implementation
"""
import pprint as pp
import unittest
from itertools import repeat

from constants import *
from room import *


class Test_ChatRoom(unittest.TestCase):
    """Test class for ChatRoom class methods
    tests for connecting to mongodb and sending and retrieving messages
    from the database
    """

    def setUp(self):
        """ initializes tests
            Set up a ChatRoom instance for both public and private rooms
        """
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, filename="room_test.log")
        self.room_list = RoomList(DEFAULT_ROOM_LIST_NAME)
        self.users = UserList(DEFAULT_USER_LIST_NAME)
        self.room = ChatRoom(PUBLIC_ROOM_NAME, [], USER_ALIAS, ROOM_TYPE_PUBLIC, True)
        self.room_list.add(self.room)

    def test_get_messages(self):
        """ test getting 20 messages
        """
        LOGGER.debug("entering test_get_messages")
        message_list = self.room_list.find(PUBLIC_ROOM_NAME).get_messages(20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))

    def test_send_message(self):
        """test sending one basic message
        """
        LOGGER.debug("entering test_send_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE}\''))
        
        
    def test_send_empty_message(self):
        """test sending one empty message
        """
        LOGGER.debug("entering test_send_empty_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_EMPTY, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_EMPTY}\''))
        
        
    def test_send_short_message(self):
        """test sending one short message
        """
        LOGGER.debug("entering test_send_short_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_SHORT, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_SHORT}\''))
        
        
    def test_send_long_message(self):
        """test sending one long message
        """
        LOGGER.debug("entering test_send_long_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_LONG, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_LONG}\''))
        
    
    def test_send_number_message(self):
        """test sending one number message
        """
        LOGGER.debug("entering test_send_number_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_NUMBERS, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_NUMBERS}\''))
        

    def test_send_receive_message(self):
        """test sending and receiving a message
        """
        LOGGER.debug("entering test_send_receive_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE, mess_props))
        message_list = self.room_list.find(PUBLIC_ROOM_NAME).get_messages(20, False)
        self.assertIsNot(message_list, [])
        
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE, message_list)

    def test_send_receive_multiple_messages(self):
        """test sending and receiving 10 messages
        """
        LOGGER.debug('entering test_send_receive_multiple_messages')
        for loop_control in range(0, 10):
            mess_props = MessageProperties(
                PUBLIC_ROOM_NAME,
                SENT_MESSAGE,
                USER_ALIAS,
                USER_ALIAS,
                datetime.now(),
                None,
                -1,
            )
            self.assertTrue(
                self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE, mess_props)
            )
        message_list = self.room_list.find(PUBLIC_ROOM_NAME).get_messages(1000, False)
        self.assertIsNot(message_list, [])
        
        LOGGER.debug(pp.pformat(message_list))
        self.assertTrue(set(repeat(TEST_MESSAGE, 10)).issubset(message_list))

        
    def test_send_receive_empty_message(self):
        """test sending one empty message
        """
        LOGGER.debug("entering test_send_empty_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_EMPTY, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_EMPTY}\''))
        message_list = self.room_list.find(PUBLIC_ROOM_NAME).get_messages(20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_EMPTY, message_list)
        
    def test_send_receive_short_message(self):
        """test sending one short message
        """
        LOGGER.debug("entering test_send_short_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_SHORT, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_SHORT}\''))
        message_list = self.room_list.find(PUBLIC_ROOM_NAME).get_messages(20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_SHORT, message_list)
        
    def test_send_receive_long_message(self):
        """test sending one long message
        """
        LOGGER.debug("entering test_send_long_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_LONG, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_LONG}\''))
        message_list = self.room_list.find(PUBLIC_ROOM_NAME).get_messages(20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_LONG, message_list)
    
    def test_send_receive_number_message(self):
        """test sending one number message
        """
        LOGGER.debug("entering test_send_number_message")
        mess_props = MessageProperties(
            PUBLIC_ROOM_NAME,
            SENT_MESSAGE,
            USER_ALIAS,
            USER_ALIAS,
            datetime.now(),
            None,
            -1,
        )
        self.assertTrue(self.room_list.find(PUBLIC_ROOM_NAME).send_message(TEST_MESSAGE_NUMBERS, mess_props))
        LOGGER.debug(pp.pformat(f'sent message \'{TEST_MESSAGE_NUMBERS}\''))
        message_list = self.room_list.find(PUBLIC_ROOM_NAME).get_messages(20, False)
        self.assertIsNot(message_list, [])
        LOGGER.debug(pp.pformat(message_list))
        self.assertIn(TEST_MESSAGE_NUMBERS, message_list)
        
    def test_room_list_add(self):
        chat_room = ChatRoom(PUBLIC_ROOM_NAME, [], USER_ALIAS, USER_ALIAS, True)
        self.room_list.add(chat_room)

if __name__ == "__main__":
    unittest.main()
