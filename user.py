import bcrypt

class User:

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

    def check_password(self, password_input):
        salt = bcrypt.gensalt()
        hashedPassword = bcrypt.hashpw(password_input.encode('utf-8'), salt)
        return self.password == hashedPassword