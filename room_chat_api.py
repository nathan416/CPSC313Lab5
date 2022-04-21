""" By: Nathan Flack
    Assignment: Lab 4: Message based chat MVP2
    Class: CPSC 313- Distributed and Cloud Computing
    Due: March 20, 2022 11:59 AM

    fast api implementation for message chat
"""
import fastapi as fa
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from constants import *
from room import *
from users import *

app = fa.FastAPI()
room_list = RoomList()
users = UserList()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginForm(BaseModel):
    alias: str
    password: str


""" Some utility functions for Auth
"""


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str):
    user = users.get(username)
    if not user:
        return False
    if not verify_password(password, get_password_hash(password)):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        alias: str = payload.get("sub")
        if alias is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = users.get(target_alias=alias)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: ChatUser = Depends(get_current_user)):
    return current_user


@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}


@app.get("/")
def index():
    pass


@app.get("/messages", status_code=200)
def receive_messages(room_name: str, messages_to_get: int):
    """api endpoint to get messages from the MongoDB server

    Args:
        room_name (str): name of the room
        messages_to_get (int): number of messages to return from the deque

    Returns:
        list: list of ChatMessages
    """
    chat_room = room_list.find(room_name)
    return chat_room.get_messages(num_messages=messages_to_get, return_objects=False)


@app.post("/send", status_code=200)
def send_message(room_name: str, message: str, from_alias: str, to_alias: str):
    """api endpoint to send messages to the ChatRoom

    Args:
        room_name (str): name of the room
        message (str): message content
        from_alias (str): name of sender
        to_alias (str): name of receiver

    Returns:
        str: message input
    """
    chat_room = room_list.find(room_name)
    mess_props = MessageProperties(
        room_name, SENT_MESSAGE, to_alias, from_alias, datetime.now(), None, -1
    )
    chat_room.send_message(message, mess_props)
    return message


@app.get("/users/", status_code=200)
async def get_users():
    """ API for getting users
    """
    user_list = users.get_all_users()
    user_str_list = []
    for user in user_list:
        user_str_list.append(user.alias)
    return user_str_list


@app.post("/alias", status_code=201)
async def register_client(client_alias: str, group_alias: bool = False):
    """ API for adding a user alias
    """
    users.register(client_alias)


@app.post("/room", status_code=201)
async def create_room(room_name: str, owner_alias: str, room_type: int = ROOM_TYPE_PUBLIC):
    """ API for creating a room
    """
    chat_room = ChatRoom(room_name, [], owner_alias, room_type, True)
    room_list.add(chat_room)
    return


def main():
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, filename="chat.log")


if __name__ == "__main__":
    main()
