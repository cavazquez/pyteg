import socket
import threading
import json


def sender(s):
    username = input('username: ')
    username_data = json.dumps({'username': username})
    s.sendall(username_data.encode())
    while True:
        data = input()
        json_data = json.dumps({'chat': data})
        s.sendall(json_data.encode())


def receiver(s):
    data = ""
    while data != b'':
        data_b = s.recv(1024)
        data = data_b.decode()
        data_json = json.loads(data)
        if 'chat' in data_json:
            print(data_json['chat'])


def main():
    host = '127.0.0.1'  # The server's hostname or IP address
    port = 65432  # The port used by the server

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    t = threading.Thread(target=receiver, args=[s])
    t.start()
    #t = threading.Thread(target=sender, args=[s])
    #t.start()
    sender(s)


if __name__ == '__main__':
    main()
