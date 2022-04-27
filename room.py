""" By: Nathan Flack
    Assignment: Lab 5: Message based chat MVP3
    Class: CPSC 313- Distributed and Cloud Computing
    Due: April 24, 2022 11:59 AM

    Room Chat implementation
"""
from collections import deque
from datetime import datetime

from pymongo import MongoClient, ReturnDocument
import itertools

from constants import *
from users import *
from statsd import StatsClient

STATSCLIENT = StatsClient(STATS_CLIENT_IP)

LOGGER = logging.getLogger(__name__)


class MessageProperties:
    """class holding the properties of ChatMessages
    """

    def __init__(self, room_name: str, mess_type: int, to_user: str, from_user: str, sent_time: datetime, rec_time: datetime) -> None:
        self.__room_name = room_name
        self.__mess_type = mess_type
        self.__to_user = to_user
        self.__from_user = from_user
        self.__sent_time = sent_time
        self.__rec_time = rec_time

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

    def to_dict(self):
        return {
            "room_name": self.__room_name,
            "mess_type": self.__mess_type,
            "to_user": self.__to_user,
            "from_user": self.__from_user,
            "sent_time": self.__sent_time,
            "rec_time": self.__rec_time,
        }

    def __str__(self):
        return str(self.to_dict())


class ChatMessage:
    """ class for storing messages in the ChatRoom
    """

    def __init__(self, message: str, mess_id: int, mess_props: MessageProperties, sequence_num: int = -1):
        self.__message = message
        self.__mess_id = mess_id
        self.__mess_props = mess_props
        self.__sequence_num = sequence_num
        self.__dirty = True
        self.__removed = False

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

    @property
    def sequence_num(self):
        return self.__sequence_num

    @sequence_num.setter
    def sequence_num(self, new_value):
        if isinstance(new_value, int):
            self.__sequence_num = new_value

    @property
    def removed(self):
        return self.__removed

    @removed.setter
    def removed(self, new_value):
        if isinstance(new_value, bool):
            self.__removed = new_value

    @mess_id.setter
    def mess_id(self, new_value):
        if isinstance(new_value, int):
            self.__mess_id = new_value

    @dirty.setter
    def dirty(self, new_value):
        if isinstance(new_value, bool):
            self.__dirty = new_value

    def to_dict(self):
        """Controlling getting data from the class in a dictionary. Yes, I know there is a built in __dict__ but I wanted to retain control"""
        mess_props_dict = self.mess_props.to_dict()
        return {"message": self.message, "sequence_num": self.sequence_num, "removed": self.removed, "mess_props": mess_props_dict}

    def __str__(self):
        return f"Chat Message: {self.message} - message props: {self.mess_props}"


class ChatRoom(deque):
    """A chat room class to hold messages from mongodb
    """

    def __init__(self, room_name: str, member_list: list, owner_alias: str, room_type: int, create_new: bool):
        super(ChatRoom, self).__init__()
        self.__room_name = room_name
        self.__user_list = UserList()
        self.__member_list = []
        self.__owner_alias = owner_alias
        self.__room_type = room_type
        self.__removed = False

        self.__mongo_client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, username=USERNAME, password=PASSWORD, authSource='cpsc313', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client.cpsc313
        self.__mongo_collection = self.__mongo_db.get_collection(room_name)
        self.__mongo_seq_collection = self.__mongo_db.get_collection('sequence')
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(room_name)
        if owner_alias not in member_list:
            member_list.append(owner_alias)
        if create_new is True or self.__restore() is False:
            self.__room_type = room_type
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()
            self.__owner_alias = owner_alias
            self.__dirty = True
            self.__room_id = None
            self.__member_list = member_list
            self.__deleted = False
            for member in member_list:
                if self.__user_list.get(member) is not None:
                    self.add_member(member)
                else:
                    LOGGER.debug(f'Invalid alias: {member} trying to add alias to member list in chatroom constructor')

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
    def dirty(self):
        return self.__dirty

    @property
    def removed(self):
        return self.__removed

    @removed.setter
    def removed(self, new_value):
        if isinstance(new_value, bool):
            self.__removed = new_value

    def __get_next_sequence_num(self):
        """ This is the method that you need for managing the sequence. Note that there is a separate collection for just this one document
            gets the sequence collection
        """
        sequence_num = self.__mongo_seq_collection.find_one_and_update(
            {'_id': 'userid'},
            {'$inc': {self.room_name: 1}},
            projection={self.room_name: True, '_id': False},
            upsert=True,
            return_document=ReturnDocument.AFTER)
        return sequence_num

    def __get_current_sequence_num(self):
        if (sequence_num := self.__mongo_seq_collection.find_one({self.room_name: {'$exists': 'true'}})) is None:
            return -1
        return sequence_num[self.room_name]

    def find_member(self, member_name) -> str:
        for member in self.__member_list:
            if member == member_name:
                return member
        return None

    def add_member(self, member_name: str):
        """add new user to member list

        Args:
            member_name (str): user
        """
        if self.__user_list.get(member_name) is None:
            LOGGER.warning('member not found in user list')
            return 10
        if self.find_member(member_name) is not None:
            LOGGER.debug('member already exists')
            return 1
        self.__member_list.append(member_name)

    def remove_group_member(self, member_name: str):
        """remove user from member list

        Args:
            member_name (str): user name
        """
        self.__member_list.remove(member_name)

    def __retrieve_messages(self):
        pass

    def find_by_sequence_num(self, sequence_num) -> ChatMessage:
        """ binary search implementation since the deque is sorted
        """
        num_messages = self.length()
        cur_low_index = 0
        cur_hi_index = num_messages - 1
        while self[cur_low_index] < sequence_num < self[cur_hi_index]:
            cur_mid = (cur_hi_index - cur_low_index) // 2
            if sequence_num < self[cur_mid].sequence_num:
                cur_hi_index = cur_mid
            elif sequence_num > self[cur_mid].sequence_num:
                cur_low_index = cur_mid
            else:  # we found it!! we can return it
                return self[cur_mid]
        return None

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

        for mess_dict in self.__mongo_collection.find({"room_name": {"$exists": False}}).sort("sequence_num", 1):
            new_mess_props = MessageProperties(
                mess_dict["mess_props"]["room_name"],
                mess_dict["mess_props"]["mess_type"],
                mess_dict["mess_props"]["to_user"],
                mess_dict["mess_props"]["from_user"],
                mess_dict["mess_props"]["sent_time"],
                mess_dict["mess_props"]["rec_time"],
            )
            new_message = ChatMessage(mess_dict["message"], mess_dict["_id"], new_mess_props, mess_dict["sequence_num"])
            new_message.dirty = False
            self.put(new_message)
        return True

    def persist(self):
        """First save a document that describes the room list (metadata: name of list, create and modify times) if it isn't already there
        Second, for each message in the list create and save a document for that message
            NOTE: We're using our custom to_dict so we give Mongo what it wants
        """
        LOGGER.info("Starting persist")
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
                'deleted': self.__deleted,
                "create_time": self.__create_time,
                "modify_time": self.__modify_time,
            }, upsert=True)
        self.__dirty = False
        for message in list(self):
            if message.dirty:
                if message.mess_id is None or self.__mongo_collection.find_one({'_id': message.mess_id}) is None:
                    message.sequence_num = self.__get_next_sequence_num()[self.room_name]
                    serialized = message.to_dict()
                    message.mess_id = self.__mongo_collection.insert_one(serialized).inserted_id
                else:
                    serialized = message.to_dict()
                    self.__mongo_collection.replace_one({'id': message.mess_id}, serialized, upsert=True)
                message.dirty = False

    @STATSCLIENT.timer('get_messages')
    def get_messages(self, user_alias: str, num_messages: int = 0, return_objects: bool=False) -> tuple:  # list of ChatMessage
        """ get a list of messages or message objects
            gets the messages from the right of the deque and doesnt display them if the sender
            of the message is in the owner's blacklist
        Args:
            num_messages (int): number of messages
            return_objects (bool): whether to get ChatMessage or str

        Returns:
            list: _description_
        """
        LOGGER.info('starting get_messages')
        if user_alias not in self.member_list:  # TODO: propably should throw an exception here
            LOGGER.debug(f'Inside get_messages, user alias {user_alias} is not in the members list')
            return [], [], 0
        message_list = []
        message_objects = []

        for message in list(self)[-num_messages:]:
            if (user := self.__user_list.get(user_alias)) is not None:
                if message.mess_props.from_user in user.blacklist:
                    continue
            message_objects.append(message)
            message_list.append(message.message)
        STATSCLIENT.gauge('num_messages', len(message_list))
        total_messages = len(message_list)
        if return_objects is True:
            return message_list, message_objects, total_messages
        else:
            return message_list, [], total_messages

    def send_message(self, message: str, from_alias: str):
        """add a message to the room and update mongo

        Args:
            message (str): message content
            mess_props (MessageProperties): message properties

        Returns:
            bool: returns true if successful
        """
        new_mess_props = MessageProperties(
                room_name = self.room_name,
                mess_type = MESSAGE_TYPE_SENT,
                to_user = self.room_name,
                from_user = from_alias,
                sent_time = datetime.now(),
                rec_time = None,
            )
        message_object = ChatMessage(message, None, new_mess_props)
        put_success = self.put(message_object)
        self.persist()
        return put_success

    def find_message(self, message_text: str) -> ChatMessage:
        """ search for a message by text and return the ChatMessage object
            doesnt display them if the sender
            of the message is in the owner's blacklist
        Args:
            message_text (str): search content

        Returns:
            ChatMessage: return object
        """
        for message in super():
            if message_text == message.message and message.from_user not in self.__user_list.get(self.__owner_alias).blacklist:
                return message
        LOGGER.warning(f"{message_text} not found")

    def find_messages_by_user(self, user: str) -> list:
        """ search for a message by sender and return the list of ChatMessage objects
            doesnt display them if the sender
            of the message is in the owner's blacklist
        Args:
            user (str): search content

        Returns:
            list: list of ChatMessage objects
        """
        message_list = []
        for message in super():
            if user == message.from_user and message.from_user not in self.__user_list.get(self.__owner_alias).blacklist and not message.removed:
                message_list.append(message)
        return message_list

    def remove_messages_by_user(self, user: str) -> list:
        """ search for a message by sender and return the list of ChatMessage objects
            doesnt display them if the sender
            of the message is in the owner's blacklist
        Args:
            user (str): search content

        Returns:
            list: list of ChatMessage objects
        """
        message_list = []
        for message in super():
            if user == message.from_user and message.from_user not in self.__user_list.get(self.__owner_alias).blacklist:
                message.removed = True
        return message_list

    def get(self) -> ChatMessage:
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
        self.__name = name
        self.__room_list = list()
        self.__rooms_metadata = list()
        self.__mongo_client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, username=USERNAME, password=PASSWORD, authSource='cpsc313', authMechanism='SCRAM-SHA-256')
        self.__mongo_db = self.__mongo_client[MONGO_DB_NAME]
        self.__mongo_collection = self.__mongo_db[DEFAULT_ROOM_LIST_NAME]

        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(self.name)

        if not self.__restore():
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()
            self.__dirty = True
            self.__persist()
        else:
            self.__dirty = False

    @property
    def name(self):
        return self.__name

    @property
    def room_list(self):
        return self.__room_list

    def create(self, room_name: str, owner_alias: str, member_list: list = None, room_type: int = ROOM_TYPE_PRIVATE) -> ChatRoom:
        """ Create a new chatroom. First check to see if a room exists with that name, and if so, bail. """
        if self.get(room_name=room_name) is not None:
            LOGGER.debug(f'Trying to create, room_name: {room_name} already exists')
            return None
        new_room = ChatRoom(room_name=room_name, owner_alias=owner_alias, member_list=member_list, room_type=room_type, create_new=True)
        self.add(new_room=new_room)
        return new_room

    def add(self, new_room: ChatRoom):
        """adds ChatRoom object to the room list after checking if it already exists.

        Args:
            new_room (ChatRoom): room to be added to the room list
        """
        if self.get(room_name=new_room.room_name) is not None:
            LOGGER.debug(f'Trying to add, room_name: {new_room.room_name} already exists')
            return

        self.__room_list.append(new_room)
        if self.find_room_in_metadata(new_room.room_name) is None:
            self.__rooms_metadata.append({'room_name': new_room.room_name, 'room_type': new_room.room_type, 'owner_alias': new_room.owner_alias, 'member_list': new_room.member_list})
        self.__modify_time = datetime.now()
        self.__dirty = True
        self.__persist()

    def find_room_in_metadata(self, room_name: str) -> dict:
        for room_dict in self.__rooms_metadata:
            if room_dict['room_name'] == room_name:
                return room_dict
        return None

    def remove(self, room_name: str):
        """remove first occurrence of a room matching the given room_name

        Args:
            room (str): name of room
        """
        for room in self.__room_list:
            if room.room_name == room_name:
                room.removed = True
                self.__modify_time = datetime.now()
                self.__persist()
                return
        LOGGER.warning(f'Room {room} not found in {self.__room_list}')

    def get(self, room_name: str) -> ChatRoom:
        """Find a room by the room name

        Args:
            room_name (str): search name

        Returns:
            ChatRoom: found object
        """
        for room in self.__room_list:
            if room.room_name == room_name and not room.removed:
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
            if found_member is not None and not room.removed:
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
            if room.owner_alias == owner and not room.removed:
                found_room_list.append(room)
        return found_room_list

    def __persist(self):
        """ Save a document that describes the room list (name of list, create, modify times, and metadata).
        """
        LOGGER.info("Persisting room data to Mongo")
        if (self.__mongo_collection.find_one({"list_name": self.__name}) is None):
            self.__mongo_collection.insert_one(
                {
                    "list_name": self.__name,
                    "create_time": self.__create_time,
                    "modify_time": self.__modify_time,
                    "rooms_metadata": self.__rooms_metadata,
                }
            )
        elif self.__dirty:
            self.__mongo_collection.replace_one({"list_name": self.__name},
                                                {
                "list_name": self.__name,
                "create_time": self.__create_time,
                "modify_time": self.__modify_time,
                "rooms_metadata": self.__rooms_metadata,
            }, upsert=True)
        for room in self.__room_list:
            if room.dirty is True:
                room.persist()
        LOGGER.info("Done persisting room data to Mongo")

    def __restore(self):
        """ Get the document for the list itself, which will have the room list metadata
        """
        LOGGER.info("Restoring room list from Mongo")
        list_data = self.__mongo_collection.find_one({"list_name": {"$exists": 'true'}})
        if list_data is None:
            LOGGER.warning("room list not found")
            return False
        self.__name = list_data['list_name']
        self.__list_id = list_data['_id']
        self.__create_time = list_data['create_time']
        self.__modify_time = list_data['modify_time']
        self.__rooms_metadata = list_data['rooms_metadata']
        for room_dict in self.__rooms_metadata:
            if (new_room := ChatRoom(room_name=room_dict['room_name'], owner_alias=room_dict['owner_alias'], member_list=room_dict['member_list'], room_type=room_dict['room_type'], create_new=False)) is None:
                new_room = self.create(room_name=room_dict['room_name'], owner_alias=room_dict['owner_alias'], member_list=room_dict['member_list'], room_type=room_dict['room_type'])
            self.add(new_room=new_room)
        LOGGER.info("Done restoring room list from Mongo")
        return True


def main():
    pass


if __name__ == "__main__":
    main()
