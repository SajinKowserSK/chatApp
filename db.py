from pymongo import MongoClient
import bcrypt
import datetime as dt
from bson import ObjectId

from user import User

# get the cluster
client = MongoClient("mongodb+srv://adminUser:password_123@chatapp-ubwoq.mongodb.net/test?retryWrites=true&w=majority")
# get database
chat_db = client.get_database("ChatDB")
# get the collection within database
users_collection = chat_db.get_collection("users")
rooms_collection = chat_db.get_collection("rooms")
room_members_collection = chat_db.get_collection("room_members")

# given username, creates collection with username as primary key, email field and password field (hashed pwd)
def save_user(username, email, password):
    salt = bcrypt.gensalt()
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), salt)
    # insert a dict with params
    users = users_collection.insert_one({'_id': username, 'email': email, 'password': hashedPassword})


# given userID, finds info related to that primary key and creates user class with it
def get_user(username):
    foundUser = users_collection.find_one({'_id': username})
    if foundUser:
        return User(foundUser['_id'], foundUser['email'], foundUser['password'])

    else:
        return None

# similiar to saving a user
def save_room(room_name, create_by):

    room_id = rooms_collection.insert_one({'room_name': room_name, 'created_by': create_by,
                                           'created_at': dt.datetime.now()}).inserted_id

    add_room_member(room_id, room_name, create_by, create_by, is_room_admin=True)
    return room_id

# first find the room, with a dict then another dict with {'$set': {updateDict}}
# def update_room(room_id, room_name):
#     rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set':{'name': room_name}})

def update_room(room_id, room_name):
    rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set': {'name': room_name}})
    room_members_collection.update_many({'_id.room_id': ObjectId(room_id)}, {'$set': {'room_name': room_name}})

# simple find_one called on collection to find room where object id equal to param
def get_room(room_id):
    rooms_collection.find_one({'id': ObjectId(room_id)})


# because our schema says room_member id is (room_id, username, make sure we do collection.insert({'_id': { room_id, username}, 'room_name', etc.
def add_room_member(room_id, room_name, username, added_by, is_room_admin=False):
    room_members_collection.insert({'id':{'room_id':room_id, 'username': username},
    'room_name': room_name, 'added_by':added_by, 'added_at':dt.datetime.now(), 'is_room_admin':is_room_admin})

def add_room_members(room_id, room_name, usernames, added_by):
    room_members_collection.insert_many(
        [{'id':{'room_id':room_id, 'username': username},
    'room_name': room_name, 'added_by':added_by, 'added_at':dt.datetime.now(), 'is_room_admin':False} for username in usernames]
    )

def remove_room_members(room_id, usernames):
    # have to use mongo db $in function here because the id can be multiple things (room id or usernames)
    room_members_collection.delete_many({'_id': {'$in': [{'room_id': room_id, 'username': username} for username in usernames]}})

def get_room_members(room_id):
    room_members_collection.find({'_id.room_id': ObjectId(room_id)})

def get_rooms_for_user(username):
    return list(room_members_collection.find({'id.username': username}))

def is_room_member(room_id, username):
    room_members_collection.count_documents({'_id': {'room_id':ObjectId(room_id), 'username': username}})

def is_room_admin(room_id, username):
    rooms_collection.count_documents({'_id': {'room_id':ObjectId(room_id), 'username': username}, 'is_room_admin': True})
