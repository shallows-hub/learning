import socket


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
            print('Connected by', addr)
            self.handle_request(conn)
        self.connect.close()

    def handle_request(self, conn):
        data = conn.recv(1024)
        print(data)
        # time.sleep(5)
        conn.close()


if __name__ == "__main__":
    server = SimpleServer("localhost", 8000)
    server.serve_forever()
