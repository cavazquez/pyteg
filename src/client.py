import socket
import threading


def sender(s):
    while True:
        data = input()
        s.sendall(data.encode())


def receiver(s):
    while True:
        data = s.recv(1024)
        print(data)


def main():
    host = '127.0.0.1'  # The server's hostname or IP address
    port = 65432  # The port used by the server

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    t = threading.Thread(target=receiver, args=[s])
    t.start()
    t = threading.Thread(target=sender, args=[s])
    t.start()


if __name__ == '__main__':
    main()
