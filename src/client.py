import socket
import threading
import json

class Connection:

    def __init__(self, host='127.0.0.1', port=65432):
        self._socket  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))

    def send_data(self, data):
        self._socket.sendall(data)

    def get_data(self):
        return self._socket.recv(1024)


def sender(connection):
    username = input('username: ')
    username_data = json.dumps({'username': username})
    # s.sendall(username_data.encode())
    connection.send_data(username_data.encode())
    while True:
        data = input()
        json_data = json.dumps({'chat': data})
        # s.sendall(json_data.encode())
        connection.send_data(json_data.encode())


def receiver(connection):
    data = ""
    while data != b'':
        # data_b = s.recv(1024)
        data_b =  connection.get_data()
        data = data_b.decode()
        data_json = json.loads(data)
        if 'chat' in data_json:
            print(data_json['chat'])


def main():
    # host = '127.0.0.1'  # The server's hostname or IP address
    # port = 65432  # The port used by the server

    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect((host, port))
    connection = Connection()
    t = threading.Thread(target=receiver, args=[connection])
    t.start()
    print(t)
    # t = threading.Thread(target=sender, args=[s])
    # t.start()
    sender(connection)


if __name__ == '__main__':
    main()
