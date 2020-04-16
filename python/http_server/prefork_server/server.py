import socket
import os
import sys
import signal
import select


class PreforkServer():

    def __init__(self, host, port, worker=5):
        self.host = host
        self.port = port
        signal.signal(signal.SIGCHLD, self._handle_chld)
        signal.signal(signal.SIGINT, self._handle_exit)
        self.workers = set()
        self.work_num = worker
        self.alive = True
        self.pipe = os.pipe()

    def _handle_chld(self, sig, frame):
        # 可能不止一个子进程在等待，循环处理僵尸进程
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except OSError:
                return
            if pid == 0:
                return

    def _handle_exit(self, sig, frame):
        for pid in self.workers:
            os.kill(pid, sig)
        self.workers.remove(pid)
        os.write(self.pipe[1], b'.')

    def spawn_worker(self):
        # 子进程才处理请求，本进程作管理进程
        for i in range(self.work_num):
            pid = os.fork()
            if pid == 0:
                worker = Worker(self.sock)
                worker.run()
                sys.exit(0)
            else:
                self.workers.add(pid)

    def serve_forever(self):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        # 设置为非阻塞，避免accept时被阻塞
        sock.setblocking(0)
        sock.listen()
        self.sock = sock
        self.spawn_worker()
        # 一般来说这里会循环管理进程，有意外结束的进程会重新启动，这里一直阻塞等待结束
        select.select([self.pipe[0]], [], [])
        sys.exit(0)


class Worker():
    def __init__(self, sock):
        self.alive = True
        self._sock = sock
        # 有INT信号时用pipe来唤醒进程直接退出
        self.pipe = os.pipe()
        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, sig, frame):
        self.alive = False
        # 让进程从阻塞状态返回
        os.write(self.pipe[1], b'1')

    def _sleep(self):
        event = select.select([self._sock, self.pipe[0]], [], [])
        if event[0]:
            if self.pipe[0] in event[0]:
                os.read(self.pipe[0], 1)

    def run(self):
        while self.alive:
            self._sleep()
            # time.sleep(2)
            try:
                client, addr = self._sock.accept()
                client.setblocking(1)
                self.handle_request(client)
                continue
            except BlockingIOError:
                # 本例子只是个简单的demo，只处理BlockingIOError
                print("sleep")
        self._sock.close()

    def handle_request(self, conn):
        # 这里简单的返回
        data = conn.recv(1024)
        print(data)
        http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
        conn.sendall(http_response)
        conn.close()


if __name__ == "__main__":
    server = PreforkServer("localhost", 8000)
    server.serve_forever()
