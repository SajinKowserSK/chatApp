from pymongo import MongoClient
import bcrypt

from user import User

# get the cluster
client = MongoClient("mongodb+srv://adminUser:password_123@chatapp-ubwoq.mongodb.net/test?retryWrites=true&w=majority")
# get database
chat_db = client.get_database("ChatDB")
# get the collection within database
users_collection = chat_db.get_collection("users")

# given username, creates collection with username as primary key, email field and password field (hashed pwd)
def save_user(username, email, password):
    salt = bcrypt.gensalt()
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), salt)
    users = users_collection.insert_one({'_id': username, 'email': email, 'password': hashedPassword})

save_user('sajinkowsersk', 'sajinkowser@gmail.com', 'shajin123')

# given userID, finds info related to that primary key and creates user class with it
def get_user(username):
    foundUser = users_collection.find_one({'_id': username})
    if foundUser:
        return User(foundUser['_id'], foundUser['email'], foundUser['password'])

    else:
        return None


