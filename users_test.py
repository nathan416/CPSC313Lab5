import unittest
from unittest import TestCase
from constants import *
from users import *

class UserTest(TestCase):
    """ Docstring
    """
    def setUp(self) -> None:
#        super().__init__(methodName)
        logging.basicConfig(
            level=logging.DEBUG, format=LOG_FORMAT, filename="user_test.log"
        )
        self.__cur_users = UserList(DEFAULT_USER_LIST_NAME)

    @property
    def users(self):
        return self.__cur_users

    def test_adding(self):
        LOGGER.info("Testing adding users")
        self.assertIsInstance(self.__cur_users.register(USER_ALIAS), ChatUser)
        user = self.__cur_users.get(USER_ALIAS)
        self.assertIsInstance(user, ChatUser)
        self.assertEqual(user.alias, USER_ALIAS)
        LOGGER.info("done testing adding users")

    def test_getting(self):
        LOGGER.info("Testing getting users")
        self.assertIsInstance(self.__cur_users.register(USER_ALIAS + '0'), ChatUser)
        self.assertIsInstance(self.__cur_users.register(USER_ALIAS + '1'), ChatUser)
        self.assertIsInstance(self.__cur_users.register(USER_ALIAS + '2'), ChatUser)
        self.assertIsInstance(self.__cur_users.register(USER_ALIAS + '3'), ChatUser)
        
        user0 = self.__cur_users.get(USER_ALIAS + '0')
        user1 = self.__cur_users.get(USER_ALIAS + '1')
        user2 = self.__cur_users.get(USER_ALIAS + '2')
        user3 = self.__cur_users.get(USER_ALIAS + '3')
        
        self.assertIsInstance(user0, ChatUser)
        self.assertIsInstance(user1, ChatUser)
        self.assertIsInstance(user2, ChatUser)
        self.assertIsInstance(user3, ChatUser)
        
        self.assertEqual(user0.alias, USER_ALIAS + '0')
        self.assertEqual(user1.alias, USER_ALIAS + '1')
        self.assertEqual(user2.alias, USER_ALIAS + '2')
        self.assertEqual(user3.alias, USER_ALIAS + '3')
        LOGGER.info("done testing getting users")
        
    def test_get_all_users(self):
        user_list = self.__cur_users.get_all_users()
        LOGGER.debug(user_list)
    
if __name__ == "__main__":
    unittest.main()