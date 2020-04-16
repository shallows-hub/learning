import socket
import select


class SimpleServer():

    def __init__(self, host, port):
        self.connect = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        # 处理TIME_WAIT
        self.connect.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connect.bind((host, port))

    def serve_forever(self):
        self.connect.listen()
        while 1:
            try:
                conn, addr = self.connect.accept()
            except KeyboardInterrupt:
                break
            self.handle_request(conn)
        self.connect.close()

    def handle_request(self, sock):
        while True:
            ready = select.select([sock], [], [], 1)
            if ready:
                data = sock.recv(1024)
                if data == b"":
                    break
                else:
                    print(data)


if __name__ == "__main__":
    server = SimpleServer("localhost", 8000)
    server.serve_forever()
