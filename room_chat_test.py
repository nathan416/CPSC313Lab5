""" By: Nathan Flack
    Assignment: Lab 4: Message based chat MVP2
    Class: CPSC 313- Distributed and Cloud Computing
    Due: March 20, 2022 11:59 AM

    tests for fast api implementation of message chat
"""
import json
import requests
import unittest
from constants import *
import pprint as pp

MESSAGES = ["first"]
NUM_MESSAGES = 4

class TestChatRoomAPI(unittest.TestCase):
    """ Test client for API testing.
        using unittest and the TestCase base class 
    """
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, filename='room_chat_test.log')
    
    def test_send(self):
        """ Test sending. This is a very simple placeholder for what would ultimately be quite a few tests for send. We're only testing a trival single send
                TODO: normally we would test various send patterns:
                1) sending data we know about, should include: empty string, short string, long string, numbers, etc
                2) sending lots of messages quickly
                3) sending batches of random size
                4) What does a mini-DOS attack do?
            Simple loop through a number of messages, sending them through the api. 
                NOTE: In this case I'm using the requests library instead of fastAPI testclient. This requires the server to be running in advance
                TODO: switch to fastAPI test client so that the server gets managed for me by fastAPI. Both tests are interesting.
        """
        LOGGER.debug('Entering test_send method')
        for loop_control in range(0, NUM_MESSAGES):
            LOGGER.debug(f'Inside loop in test_send, iteration is {loop_control}')
            response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE} {loop_control}&from_alias=test&to_alias={USER_ALIAS}')
            try: 
                self.assertEqual(response.status_code, 201)
            except: 
                LOGGER.debug(f'test for message number {loop_control} failed. Response status: {response.status_code}. Total response: {response}')
    
    
    def test_send_empty_message(self):
        """test sending one empty message
        """
        LOGGER.debug("entering test_send_empty_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_EMPTY}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)
        
    def test_send_short_message(self):
        """test sending one short message
        """
        LOGGER.debug("entering test_send_short_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_SHORT}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)
        
    def test_send_long_message(self):
        """test sending one long message
        """
        LOGGER.debug("entering test_send_long_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_LONG}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)
    
    def test_send_number_message(self):
        """test sending one number message
        """
        LOGGER.debug("entering test_send_number_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_NUMBERS}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        """ Simple get tests. Again, very simple placeholder for what would be much more interesting receive tests
                TODO: normally we would test various get patterns:
                1) getting data we know about (we sent it), should include: empty string, short string, long string, numbers, etc
                2) receiving all messages
                3) receiving batches of 1 and random sizes
                4) What does a mini-DOS attack do for receiving do?
            Simple get messages method call, then loop through messages returned logging them.
                NOTE: In this case I'm using the requests library instead of fastAPI testclient. This requires the server to be running in advance
                TODO: switch to fastAPI test client so that the server gets managed for me by fastAPI. Both tests are interesting.
        """
        LOGGER.debug('Entering test get method')
        response = requests.get(f'http://localhost:8000/messages?room_name={PUBLIC_ROOM_NAME}&messages_to_get=10')
        try: 
            self.assertEqual(response.status_code, 200)
            message_list = json.loads(response.content)
            for message in message_list:
                LOGGER.debug(f'Inside loop in test get, message is {message}')
            return response.text
        except: 
            LOGGER.warning(f'test for getting messages failed. Response status: {response.status_code}. Total response: {response}')

    def test_send_receive(self):
        """ Method for testing that what we send, we receive on the other end
            TODO: Flesh this out, and flesh out a bunch of specialized test cases for this pattern

        """
        try:
            response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message=test send and receive&from_alias=test&to_alias={USER_ALIAS}')
            LOGGER.debug(f'Inside full test for ChatRoom, send_result is: {response}')
            self.assertIsNotNone(response)
        except AssertionError as problem:
            LOGGER.warning(f"SEND ERROR:: inside FULL test. Problem is {problem}")
        try:
            response = requests.get(f'http://localhost:8000/messages?room_name={PUBLIC_ROOM_NAME}&messages_to_get=2')
            LOGGER.debug(f'Inside full test for ChatRoom, get_result is: {response}')
            self.assertIsNotNone(response)
            message_list = json.loads(response.content)
        except AssertionError as problem:
            LOGGER.warning(f'GET ERROR:: Inside FULL test. Problem is {problem}')
        try:
            self.assertIn('test send and receive', message_list)
        except AssertionError as problem:
            LOGGER.warning(f'E2E ERROR:: Inside FULL test. Problem is {problem}')
    
    def test_send_receive_empty_message(self):
        """test sending and receiving one empty message
        """
        LOGGER.debug("entering test_send_empty_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_EMPTY}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)
        
        response2 = requests.get(f'http://localhost:8000/messages?room_name={PUBLIC_ROOM_NAME}&messages_to_get=200')
        LOGGER.debug(f'Inside full test for ChatRoom, get_result is: {response2}')
        self.assertIsNotNone(response2)
        self.assertEqual(response2.status_code, 200)
        message_list = json.loads(response2.content)
        self.assertIn(TEST_MESSAGE_EMPTY, message_list)
        
    def test_send_receive_short_message(self):
        """test sending and receiving one short message
        """
        LOGGER.debug("entering test_send_short_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_SHORT}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)

        response2 = requests.get(f'http://localhost:8000/messages?room_name={PUBLIC_ROOM_NAME}&messages_to_get=200')
        LOGGER.debug(f'Inside full test for ChatRoom, get_result is: {response2}')
        self.assertIsNotNone(response2)
        self.assertEqual(response2.status_code, 200)
        message_list = json.loads(response2.content)
        self.assertIn(TEST_MESSAGE_SHORT, message_list)
        
    def test_send_receive_long_message(self):
        """test sending and receiving one long message
        """
        LOGGER.debug("entering test_send_long_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_LONG}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)

        response2 = requests.get(f'http://localhost:8000/messages?room_name={PUBLIC_ROOM_NAME}&messages_to_get=200')
        LOGGER.debug(f'Inside full test for ChatRoom, get_result is: {response2}')
        self.assertIsNotNone(response2)
        self.assertEqual(response2.status_code, 200)
        message_list = json.loads(response2.content)
        self.assertIn(TEST_MESSAGE_LONG, message_list)
    
    def test_send_receive_number_message(self):
        """test sending and receiving one number message
        """
        LOGGER.debug("entering test_send_number_message")
        response = requests.post(f'http://localhost:8000/send?room_name={PUBLIC_ROOM_NAME}&message={TEST_MESSAGE_NUMBERS}&from_alias=test&to_alias={USER_ALIAS}')
        self.assertEqual(response.status_code, 200)

        response2 = requests.get(f'http://localhost:8000/messages?room_name={PUBLIC_ROOM_NAME}&messages_to_get=200')
        LOGGER.debug(f'Inside full test for ChatRoom, get_result is: {response2}')
        self.assertIsNotNone(response2)
        self.assertEqual(response2.status_code, 200)
        message_list = json.loads(response2.content)
        self.assertIn(TEST_MESSAGE_NUMBERS, message_list)
        
    def test_get_users(self):
        """testing the api get call to /users
        """
        LOGGER.debug("entering test_get_users")
        response = requests.get(f'http://localhost:8000/users/')
        LOGGER.debug(response.content)
        self.assertEqual(response.status_code, 200)
    
    def test_register_users(self):
        """testing the api post call to /alias
        """
        LOGGER.debug("entering test_register_users")
        response = requests.post(f'http://localhost:8000/alias?client_alias={USER_ALIAS}/')
        self.assertEqual(response.status_code, 201)
    
    def test_room_create(self):
        """testing the api post call to /room
        """
        LOGGER.debug("entering test_room_create")
        response = requests.post(f'http://localhost:8000/room?room_name={PUBLIC_ROOM_NAME}&owner_alias={USER_ALIAS}&room_type={ROOM_TYPE_PUBLIC}')
        self.assertEqual(response.status_code, 201)

if __name__ == "__main__":
    unittest.main()
            

        

