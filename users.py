import queue
from constants import *
from datetime import date, datetime
from pymongo import MongoClient
from constants import *
        
class ChatUser():
    """ class for users of the chat system. Users must be registered 
    """
    def __init__(self, alias: str, user_id = None, create_time: datetime = datetime.now(), modify_time: datetime = datetime.now()) -> None:
        self.__alias = alias
        self.__user_id = user_id 
        self.__create_time = create_time
        self.__modify_time = modify_time
        if self.__user_id is not None:
            self.__dirty = False
        else:
            self.__dirty = True

    @property
    def alias(self):
        return self.__alias
    
    @property
    def dirty(self):
        return self.__dirty
    
    @dirty.setter
    def dirty(self, new_value):
        if type(new_value) is bool:
            self.__dirty = new_value
    
    def to_dict(self):
        return {
                'alias': self.__alias,
                'create_time': self.__create_time,
                'modify_time': self.__modify_time
        }
    
    def __str__(self):
        return self.__alias
        
class UserList():
    """ List of users, inheriting list class
    """
    def __init__(self, list_name: str = DEFAULT_USER_LIST_NAME) -> None:
        self.__user_list = list()
        self.__mongo_client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, username=USERNAME, password=PASSWORD, authSource='cpsc313', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client['cpsc313']
        self.__mongo_collection = self.__mongo_db['users']
        if self.__restore():
#            raise Exception('No name and no document to restore')
            self.__dirty = False
        else:
            self.__name = list_name
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()
            self.__dirty = True

    
    def register(self, new_alias: str) -> ChatUser:
        """
        """
        LOGGER.info(f"Registering {new_alias} in {self.__name}")
        user = self.get(new_alias)
        if user is not None:
            LOGGER.warning(f'User {new_alias} already registered')
            return user
        new_user = ChatUser(new_alias)
        self.append(new_user)
        self.__persist()
        return new_user
        

    def get(self, target_alias: str) -> ChatUser:
        LOGGER.info(f"Getting User {target_alias} from {self.__name}")
        for user in self.__user_list:
            if user.alias == target_alias: 
                return user
        LOGGER.warning(f"User {target_alias} not found")
        return None

    def get_all_users(self) -> list:
        return self.__user_list

    def append(self, new_user: ChatUser) -> None:
        self.__user_list.append(new_user)

    def __restore(self) -> bool:
        """ First get the document for the list itself, then get all documents that are not the list metadata
        """
        LOGGER.info("Restoring user list from Mongo")
        list_data = self.__mongo_collection.find_one({"list_name": {"$exists": True}})
        if list_data is None:
            LOGGER.warning("User list not found")
            return False
        self.__name = list_data["list_name"]
        self.__create_time = list_data["create_time"]
        self.__modify_time = list_data["modify_time"]
        for user_dict in self.__mongo_collection.find({"list_name": {"$exists": False}}):
            new_user = ChatUser(alias = user_dict["alias"], user_id = user_dict["_id"], create_time = user_dict["create_time"], modify_time = user_dict["modify_time"])
            new_user.dirty = False
            self.append(new_user)
        LOGGER.info("Done restoring user list from Mongo")
        return True

    def __persist(self):
        """ First save a document that describes the user list (name of list, create and modify times)
            Second, for each user in the list create and save a document for that user
        """
        LOGGER.info("Persisting data to Mongo")
        if (self.__mongo_collection.find_one({"list_name": self.__name}) is None):
            self.__mongo_collection.insert_one(
                {
                    "list_name": self.__name,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                }
            )
        else:
            self.__mongo_collection.replace_one({"list_name": self.__name},
                {
                    "list_name": self.__name,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                }, upsert=True)
        self.dirty = False
        for user in self.__user_list:
            if user.dirty:
                serialized2 = user.to_dict()
                self.__mongo_collection.insert_one(serialized2)
                user.dirty = False
        LOGGER.info("Done persisting data to Mongo")
    
    def remove(self, user: str) -> None:
        self.__user_list.remove(user)
        
    def to_dict(self):
        return self.__user_list