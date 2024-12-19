class Client:
    def __init__(self):
        self._username = None
        self._userid = None
        self._es_admin = False

    def set_username(self, username):
        self._username = username

    def set_userid(self, userid):
        self._userid = userid

    def username(self):
        return self._username

    def userid(self):
        return self._userid

    def es_admin(self):
        return self._es_admin

    def ahora_es_admin(self):
        self._es_admin = True
