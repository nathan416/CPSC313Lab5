import queue
from constants import *
from datetime import date, datetime
from pymongo import MongoClient
from constants import *


class ChatUser():
    """ class for users of the chat system. Users must be registered 
    """

    def __init__(self, alias: str, password: str = "", user_id = None, email: str = "", blacklist: list = [], create_time: datetime = datetime.now(), modify_time: datetime = datetime.now()) -> None:
        self.__alias = alias
        self.__user_id = user_id 
        self.__email = email
        self.__create_time = create_time
        self.__modify_time = modify_time
        self.__hash_pass = ""
        self.__blacklist = blacklist
        self.__removed = False
        if self.__user_id is not None:
            self.__dirty = False
        else:
            self.__dirty = True

    @property
    def blacklist(self):
        return self.__blacklist

    @property
    def hash_pass(self):
        return self.__hash_pass
    
    @property
    def alias(self):
        return self.__alias

    @property
    def dirty(self):
        return self.__dirty
    
    @hash_pass.setter
    def hash_pass(self, new_pass):
        self.__hash_pass = new_pass
        
    @property
    def email(self):
        return self.__email
    
    @email.setter
    def email(self, new_email):
        self.__email = new_email

    @dirty.setter
    def dirty(self, new_value):
        if type(new_value) is bool:
            self.__dirty = new_value

    @alias.setter
    def alias(self, new_alias: str):
        if len(new_alias) > 2:
            self.__alias = new_alias
            self.__dirty = True
    
    @property
    def private_queue_name(self):
        return self.__private_queue_name

    @private_queue_name.setter
    def private_queue_name(self, new_name: str = ""):
        if len(new_name) > 2:
            self.__private_queue_name = new_name
            self.__dirty = True

    @property
    def public_queue_name(self):
        return self.__public_queue_name

    @public_queue_name.setter
    def public_queue_name(self, new_name: str = ""):
        if len(new_name) > 2:
            self.__public_queue_name = new_name    
            self.__dirty = True 
            
    @property
    def removed(self):
        return self.__removed

    @removed.setter
    def removed(self, new_value: bool):
        if type(new_value) is bool:
            self.__removed = new_value

    def add_alias_to_blacklist(self, alias) -> bool:
        if alias not in self.blacklist:
            self.blacklist.append(alias)
            self.dirty = True
            return True
        return False

    def remove_alias_from_blacklist(self, alias) -> bool:
        if alias in self.blacklist:
            self.blacklist.remove(alias)
            self.dirty = True
            return True
        return False

    def to_dict(self):
        return {
                'alias': self.__alias,
                'blacklist': self.__blacklist,
                'removed': self.__removed,
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
            
    @property
    def id(self):
        return self.__id

    @property
    def user_list(self):
        return self.__user_list
    
    @property
    def dirty(self):
        return self.__dirty

    def register(self, new_alias: str) -> ChatUser:
        """
        """
        LOGGER.info(f"Registering {new_alias} in {self.__name}")
        user = self.get(new_alias)
        if user is not None:
            LOGGER.warning(f'User {new_alias} already registered')
            return user
        if len(new_alias) > 2:
            new_user = ChatUser(new_alias)
            self.append(new_user)
        return new_user
    
    def deregister(self, alias_to_remove: str) -> ChatUser:
        """ set the removed flag to true for the user
            TODO: must remove the user from all member lists
        """
        if (user := self.get(alias_to_remove)) is None:
            return user
        user.removed = True
        return user

    def __len__(self):
        return len(self.user_list)

    def get(self, target_alias: str) -> ChatUser:
        LOGGER.info(f"Getting User {target_alias} from {self.__name}")
        for user in self.__user_list:
            if user.alias == target_alias and not user.removed:
                return user
        LOGGER.warning(f"User {target_alias} not found")
        return None

    def get_all_user_aliases(self) -> list:
        alias_list = []
        for user in self.user_list:
            if not user.removed:
                alias_list.append(user.alias)
        return alias_list

    def append(self, new_user: ChatUser) -> None:
        """appends user to internal list object and saves to mongo

        Args:
            new_user (ChatUser): _description_
        """
        if new_user is not None:
            self.__user_list.append(new_user)
            self.__dirty = True
            self.persist()

    def __restore(self) -> bool:
        """ First get the document for the list itself, then get all documents that are not the list metadata
            pulls data from mongo
        """
        LOGGER.info("Restoring user list from Mongo")
        list_data = self.__mongo_collection.find_one({"list_name": {"$exists": True}})
        if list_data is None:
            LOGGER.warning("User list not found")
            return False
        self.__name = list_data["list_name"]
        self.__id = list_data["_id"]
        self.__create_time = list_data["create_time"]
        self.__modify_time = list_data["modify_time"]
        for user_dict in self.__mongo_collection.find({"list_name": {"$exists": False}}):
            new_user = ChatUser(alias=user_dict["alias"], user_id=user_dict["_id"], create_time=user_dict["create_time"], modify_time=user_dict["modify_time"])
            new_user.dirty = False
            self.user_list.append(new_user)
        LOGGER.info("Done restoring user list from Mongo")
        return True

    def persist(self):
        """ First save a document that describes the user list (name of list, create and modify times)
            Second, for each user in the list create and save a document for that user
        """
        LOGGER.info("Persisting data to Mongo")
        if (self.__mongo_collection.find_one({"list_name": self.__name}) is None):
            self.__id = self.__mongo_collection.insert_one(
                {
                    "list_name": self.__name,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                }
            )
        else:
            if(self.__dirty):
                self.__mongo_collection.replace_one({"list_name": self.__name},
                {
                    "list_name": self.__name,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                }, upsert=True)
                self.dirty = False
        for user in self.__user_list:
            if user.dirty:
                if self.__mongo_collection.find_one({'alias': user.alias}) is None:
                        user.user_id = self.__mongo_collection.insert_one(user.to_dict())
                else:
                    self.__mongo_collection.replace_one({'_id': user.user_id}, user.to_dict(), upsert=True)
                LOGGER.debug(user.to_dict())
                user.dirty = False
        LOGGER.info("Done persisting data to Mongo")

    def remove(self, user: str) -> None:
        self.__user_list.remove(user)

    def to_dict(self):
        return self.__user_list
