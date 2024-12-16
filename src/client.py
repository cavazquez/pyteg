class Client:
    def __init__(self):
        self._mapa = ""
        self._username = None
        self._userid = None

    def set_username(self, username):
        self._username = username

    def set_userid(self, userid):
        self._userid = userid

    def username(self):
        return self._username

    def userid(self):
        return self._userid
