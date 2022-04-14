""" By: Nathan Flack
    Assignment: Lab 4: Message based chat MVP2
    Class: CPSC 313- Distributed and Cloud Computing
    Due: March 20, 2022 11:59 AM

    Room Chat implementation
"""
from collections import deque
from datetime import datetime

from pymongo import MongoClient, ReturnDocument

from constants import *
from users import *
from statsd import StatsClient

STATSCLIENT = StatsClient('34.94.46.140')


class MessageProperties:
    """class holding the properties of ChatMessages
    """
    def __init__(self, room_name: str, mess_type: int, to_user: str, from_user: str, sent_time: datetime, rec_time: datetime, sequence_number: int) -> None:
        self.__room_name = room_name
        self.__mess_type = mess_type
        self.__to_user = to_user
        self.__from_user = from_user
        self.__sent_time = sent_time
        self.__rec_time = rec_time
        self.__sequence_number = sequence_number

    @property
    def mess_type(self):
        return self.__mess_type

    @property
    def room_name(self):
        return self.__room_name

    @property
    def to_user(self):
        return self.__to_user

    @property
    def from_user(self):
        return self.__from_user

    @property
    def sent_time(self):
        return self.__sent_time

    @property
    def rec_time(self):
        return self.__rec_time

    @property
    def sequence_number(self):
        return self.__sequence_number

    def to_dict(self):
        return {
            "room_name": self.__room_name,
            "mess_type": self.__mess_type,
            "to_user": self.__to_user,
            "from_user": self.__from_user,
            "sent_time": self.__sent_time,
            "rec_time": self.__rec_time,
            "sequence_num": self.__sequence_number,
        }

    def __str__(self):
        return str(self.to_dict())


class ChatMessage:
    """ class for storing messages in the ChatRoom
    """
    def __init__(self, message: str, mess_id: int, mess_props: MessageProperties):
        self.__message = message
        self.__mess_id = mess_id
        self.__mess_props = mess_props
        self.__dirty = True

    @property
    def message(self):
        return self.__message

    @property
    def mess_id(self):
        return self.__mess_id

    @property
    def mess_props(self):
        return self.__mess_props

    @property
    def dirty(self):
        return self.__dirty
    
    @mess_id.setter
    def mess_id(self, new_value):
        if type(new_value) is int:
            self.__mess_id = new_value

    @dirty.setter
    def dirty(self, new_value):
        if type(new_value) is bool:
            self.__dirty = new_value

    def to_dict(self):
        """Controlling getting data from the class in a dictionary. Yes, I know there is a built in __dict__ but I wanted to retain control"""
        mess_props_dict = self.mess_props.to_dict()
        return {"message": self.message, "mess_props": mess_props_dict}

    def __str__(self):
        return f"Chat Message: {self.message} - message props: {self.mess_props}"


class ChatRoom(deque):
    """A chat room class to hold messages from mongodb
    """
    def __init__(self,room_name: str, member_list: list, owner_alias: str, room_type: int, create_new: bool):
        super(ChatRoom, self).__init__()
        self.__room_name = room_name
        self.__user_list = UserList()
        self.__member_list = []
        self.__owner_alias = owner_alias
        self.__room_type = room_type
        self.__create_new = create_new
        

        self.__mongo_client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, username=USERNAME, password=PASSWORD, authSource='cpsc313', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client.cpsc313
        self.__mongo_collection = self.__mongo_db.get_collection(room_name)
        self.__mongo_seq_collection = self.__mongo_db.get_collection('sequence')
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(room_name)

        if create_new or self.__restore() is False:
            self.__room_type = room_type
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()
            self.__owner_alias = owner_alias
            self.__dirty = True
            self.__member_list = member_list
        if owner_alias not in member_list:
            member_list.append(owner_alias)

    @property
    def room_name(self):
        return self.__room_name

    @property
    def member_list(self):
        return self.__member_list

    @property
    def owner_alias(self):
        return self.__owner_alias

    @property
    def room_type(self):
        return self.__room_type

    @property
    def create_new(self):
        return self.__create_new

    @property
    def dirty(self):
        return self.__dirty
    
    def __get_next_sequence_num(self):
        """ This is the method that you need for managing the sequence. Note that there is a separate collection for just this one document
        """
        sequence_num = self.__mongo_seq_collection.find_one_and_update(
                                                        {'_id': 'userid'},
                                                        {'$inc': {self.__room_name: 1}},
                                                        projection={'seq': True, '_id': False},
                                                        upsert=True,
                                                        return_document=ReturnDocument.AFTER)
        return sequence_num

    def add_group_member(self, member_name):
        """add new user to member list

        Args:
            member_name (ChatUser): user
        """
        self.__member_list.append(member_name)

    def remove_group_member(self, member_name: str):
        """remove user from member list

        Args:
            member_name (str): user name
        """
        self.__member_list.remove(member_name)

    def __retrieve_messages(self):
        pass

    def __restore(self) -> bool:
        """We're restoring data from Mongo.
        First get the metadata record, but looking for a name key with find_one. If it exists, then we have the doc. If not, bail
            Fill in the metadata (name, create, modify times - we'll do more later)
        Second, we're getting the actual messages. Now we look for the key "message". Note that we're using find so we'll get all that
            match (every document with a key called 'message')
            For each dictionary we get back (the documents), create a message properties instance and a message instance and
                put them in the deque by calling the put method
        """
        LOGGER.info("Restoring data from Mongo")
        room_metadata = self.__mongo_collection.find_one({"room_name": self.__room_name})
        if room_metadata is None:
            LOGGER.warning("Room metadata not found")
            return False
        self.__room_name = room_metadata["room_name"]
        self.__create_time = room_metadata["create_time"]
        self.__modify_time = room_metadata["modify_time"]
        self.__owner_alias = room_metadata["owner_alias"]
        self.__room_type = room_metadata["room_type"]
        self.__member_list = room_metadata["member_list"]
        self.__room_id = room_metadata['_id']
        self.__deleted = room_metadata['deleted']
        self.__dirty = False
        
        for mess_dict in self.__mongo_collection.find({"room_name": {"$exists": False}}):
            new_mess_props = MessageProperties(
                mess_dict["mess_props"]["room_name"],
                mess_dict["mess_props"]["mess_type"],
                mess_dict["mess_props"]["to_user"],
                mess_dict["mess_props"]["from_user"],
                mess_dict["mess_props"]["sent_time"],
                mess_dict["mess_props"]["rec_time"],
                mess_dict["mess_props"]["sequence_num"],
            )
            new_message = ChatMessage(mess_dict["message"], self.length(), new_mess_props)
            new_message.dirty = False
            self.put(new_message)
        return True

    def __persist(self):
        """First save a document that describes the room list (metadata: name of list, create and modify times) if it isn't already there
        Second, for each message in the list create and save a document for that message
            NOTE: We're using our custom to_dict so we give Mongo what it wants
        """
        if (self.__mongo_collection.find_one({"room_name": self.__room_name}) is None):
            self.__mongo_collection.insert_one(
                {
                    "room_name": self.__room_name,
                    "owner_alias": self.__owner_alias,
                    "room_type": self.__room_type,
                    "member_list": self.__member_list,
                    'deleted': self.__deleted,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                }
            )
        else:
            self.__mongo_collection.replace_one({"_id": self.__room_id},
                {
                    "room_name": self.__room_name,
                    "owner_alias": self.__owner_alias,
                    "room_type": self.__room_type,
                    "member_list": self.__member_list,
                    'deleted': self.deleted,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                }, upsert=True)
        self.__dirty = False
        for message in list(self):
            if message.dirty:
                message.sequence_number = self.__get_next_sequence_num()
                serialized2 = message.to_dict()
                self.__mongo_collection.insert_one(serialized2)
                message.dirty = False

    @STATSCLIENT.timer('get_messages')
    def get_messages(self, num_messages: int, return_objects: bool) -> list:  # list of ChatMessage
        """get a list of messages or message objects

        Args:
            num_messages (int): number of messages
            return_objects (bool): whether to get ChatMessage or str

        Returns:
            list: _description_
        """
        message_list = []
        if return_objects:
            for loop_control in range(min(num_messages, len(self))):
                message_list.append(super()[loop_control])
        else:
            for loop_control in range(min(num_messages, len(self))):
                message_list.append(super()[loop_control].message)
        STATSCLIENT.gauge('num_messages', len(message_list))
        return message_list

    def send_message(self, message: str, mess_props: MessageProperties) -> bool:
        """add a message to the room and update mongo

        Args:
            message (str): message content
            mess_props (MessageProperties): message properties

        Returns:
            bool: returns true if successful
        """
        message_object = ChatMessage(message, self.length(), mess_props)
        put_success = self.put(message_object)
        self.__persist()
        return put_success

    def find_message(self, message_text: str) -> ChatMessage:
        """search for a message by text and return the ChatMessage object

        Args:
            message_text (str): search content

        Returns:
            ChatMessage: return object
        """
        for message in self:
            if message_text == message.message:
                return message
        LOGGER.warning(f"{message_text} not found")

    def get(self) -> ChatMessage:  # – gets the next message in the deque from the right
        """return last object

        Returns:
            ChatMessage: return object
        """
        return super()[-1]

    def put(self, message: ChatMessage) -> bool:
        """ adds a ChatMessage to the deque
            puts message into the (left of the) deque

        Args:
            message (ChatMessage): message object

        Returns:
            bool: returns true if successful
        """
        if message is not None:
            super().appendleft(message)
            return True
        else:
            return False

    def length(self) -> int:
        return len(self)


class RoomList():
    """class to hold and manage the list of rooms available.
    """
    def __init__(self, name: str = DEFAULT_ROOM_LIST_NAME):
        self.__room_list = []
        self.__mongo_client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, username=USERNAME, password=PASSWORD, authSource='cpsc313', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client['cpsc313']
        self.__mongo_collection = self.__mongo_db['main']
        
        if not self.__restore():
            self.__name = name
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()
      

    @property
    def name(self):
        return self.__name
    
    @property
    def room_list(self):
        return self.__room_list

    def add(self, new_room: ChatRoom):
        """adds ChatRoom object to the room list after checking if it already exists. 

        Args:
            new_room (ChatRoom): room to be added to the room list
        """
        for room in self.__room_list:
            if room.room_name == new_room.room_name:
                LOGGER.warning(f'Room {new_room} already registered')
                return
        
        self.__room_list.append(new_room)
        self.__modify_time = datetime.now()
        self.__persist()

    def remove(self, room_name: str):
        """remove first occurrence of a room matching the given room_name

        Args:
            room (str): name of room
        """
        for room in self.__room_list:
            if room.room_name == room_name:
                self.__room_list.remove(room)
                self.__modify_time = datetime.now()
                self.__persist()
                return
        LOGGER.warning(f'Room {room} not found in {self.__room_list}')
    
    def find(self, room_name: str) -> ChatRoom:
        """Find a room by the room name

        Args:
            room_name (str): search name

        Returns:
            ChatRoom: found object
        """
        for room in self.__room_list:
            if room.room_name == room_name:
                return room
        LOGGER.warning(f'Room {room_name} not found in {self.__room_list}')

    def find_by_member(self, member: str) -> list:
        """ finds all rooms in the room_list that have the given member in them.
        
        Args:
            member (str): name of member

        Returns:
            list: list of rooms with member in them
        """
        found_room_list = []
        for room in self.__room_list:
            found_member = room.member_list.find(member)
            if found_member is not None:
                found_room_list.append(room)
        return found_room_list

    def find_by_owner(self, owner: str) -> list:
        """ finds all rooms in the room_list that have the given owner.
        
        Args:
            owner (str): name of owner

        Returns:
            list: list of rooms with owner in them
        """
        found_room_list = []
        for room in self.__room_list:
            if room.owner_alias == owner:
                found_room_list.append(room)
        return found_room_list

    def __persist(self):
        """ Save a document that describes the room list (name of list, create, modify times, and metadata).
        """
        LOGGER.info("Persisting room data to Mongo")
        rooms_metadata = []
        for room in self.__room_list:
            user_str_list = []
            user_list = room.member_list.get_all_users()
            for user in user_list:
                user_str_list.append(user.alias)
            rooms_metadata.append({'room_name': room.room_name, 'room_type': room.room_type, 'owner_alias': room.owner_alias, 'member_list': user_str_list,})
        
        if (self.__mongo_collection.find_one({"list_name": self.__name}) is None):
            self.__mongo_collection.insert_one(
                {
                    "list_name": self.__name,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                    "rooms_metadata": rooms_metadata,
                }
            )
        else:
            self.__mongo_collection.replace_one({"list_name": self.__name},
                {
                    "list_name": self.__name,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                    "rooms_metadata": rooms_metadata,
                }, upsert=True)
        LOGGER.info("Done persisting room data to Mongo")

    def __restore(self):
        """ Get the document for the list itself, which will have the room list metadata
        """
        LOGGER.info("Restoring room list from Mongo")
        list_data = self.__mongo_collection.find_one({"list_name": {"$exists": True}})
        if list_data is None:
            LOGGER.warning("room list not found")
            return False
        self.__name = list_data["list_name"]
        self.__create_time = list_data["create_time"]
        self.__modify_time = list_data["modify_time"]
        for room_dict in list_data["rooms_metadata"]:
            new_room = ChatRoom(room_name=room_dict["room_name"], room_type=room_dict["room_type"], owner_alias=room_dict["owner_alias"], member_list=room_dict["member_list"], create_new=False)
            self.__room_list.append(new_room)
        LOGGER.info("Done restoring room list from Mongo")
        return True


def main():
    pass


if __name__ == "__main__":
    main()
