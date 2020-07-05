from flask import Flask, render_template, request, redirect, url_for
from flask_login import current_user, login_user, login_required, logout_user, LoginManager
from flask_socketio import SocketIO, join_room, leave_room

from db import *
from pymongo.errors import DuplicateKeyError

app = Flask(__name__)
app.secret_key = "chatAppSK"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    rooms = []

    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)

    return render_template("index.html", rooms=rooms)


@app.route('/login', methods=['GET', 'POST'])

def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'Failed to login!'
    return render_template('login.html', message=message)


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/search/", methods=['GET', 'POST'])
@login_required
def search():
    if request.method  == 'POST':
        query = get_user(request.form['keywords'].strip()).username

        return render_template("search.html", mentors=query)

    else:
        return render_template("search.html")



@app.route("/create-room/", methods = ['GET', 'POST'])
@login_required
def create_room():
    message = "hello"
    if request.method == 'POST':
        roomName = request.form['room_name']
        usernames = [username.strip() for username in request.form['members'].split(',')]


        if len(roomName) and usernames:
            roomID = save_room(roomName, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)

            add_room_members(roomID, roomName, usernames, current_user.username)
            return redirect(url_for('view_room', room_id=roomID))

        else:
            message = 'failed to create room'

    return render_template("create_room.html", message=message)


@app.route('/pm/<mentor>/', methods = ['GET', 'POST'])
@login_required
def pm(mentor):

    roomName = "Private chat with " + str(mentor).capitalize()
    usernames = [current_user.username, mentor]


    roomID = save_room(roomName, current_user.username)
    if current_user.username in usernames:
        usernames.remove(current_user.username)

    add_room_members(roomID, roomName, usernames, current_user.username)
    return redirect(url_for('view_room', room_id=roomID))


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        redirect(url_for('home'))

    message=''

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            save_user(username, email, password)
            return redirect(url_for('login'))

        except DuplicateKeyError:
            message = "User already exists, choose different username"

    return render_template('signup.html', message=message)



@app.route('/rooms/<room_id>/')
@login_required
def view_room(room_id):
    room = get_room(room_id)

    # print("ROOM ID IS", room_id)
    # print("ROOM IS", room)

    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        messages = get_messages(room_id)
        return render_template('view_room.html', username=current_user.username, room=room,
                               room_members=room_members, messages = messages)

    else:
        return 'Room not found', 404


    # if username and room:
    #
    # else:
    #     return redirect(url_for('home'))


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['room'], data['message'], data['username'])
    socketio.emit('receive_message', data, room=data['room'])



@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])


@login_manager.user_loader
def load_user(username):
    return get_user(username)





if __name__ == '__main__':
    socketio.run(app, debug=True)