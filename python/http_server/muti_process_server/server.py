import socket
import os
import signal


class MutiProcessServer():

    def __init__(self, host, port):
        signal.signal(signal.SIGCHLD, self._handle_signal)
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        # 处理TIME_WAIT
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))

    def _handle_signal(self, sig, frame):
        # 处理僵尸进程 linux也可以用signal.SIG_IGN
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except OSError:
                return
            if pid == 0:
                return

    def serve_forever(self):
        self.sock.listen()
        while True:
            try:
                conn, addr = self.sock.accept()
            except KeyboardInterrupt:
                break
            pid = os.fork()
            if pid == 0:
                self.sock.close()
                print('Connected by', addr)
                self.handle_request(conn)
                conn.close()
                exit(0)
            else:
                conn.close()
        self.sock.close()

    def handle_request(self, conn):
        data = conn.recv(1024)
        print(data)
        http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
        conn.sendall(http_response)
        # time.sleep(5)


if __name__ == "__main__":
    server = MutiProcessServer("localhost", 8000)
    server.serve_forever()
