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

class Transceiver:

    @staticmethod
    def receiver(connection):
        data_b = ""
        data_json = ""
        while data_b != b'':
            data_b =  connection.get_data()
            if not data_b:
                print("socket connection broken")
                continue

            data = data_b.decode()
            data_json = json.loads(data)

            if 'chat' in data_json:
                print(data_json['chat'])

    @staticmethod
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


def main():
    connection = Connection()
    t = threading.Thread(target=Transceiver.receiver, args=[connection])
    t.start()
    Transceiver.sender(connection)
    t.join()


if __name__ == '__main__':
    main()
