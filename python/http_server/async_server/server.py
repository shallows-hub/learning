import socket
import os
import sys
import signal
import select
import selectors

running_loop = None


class IOLoop():
    def __init__(self):
        self.selector = selectors.DefaultSelector()
        self.alive = True
        self.pipe = os.pipe()

    def add_handler(self, fileobj, events, data):
        # todo: 允许多个协程对同一个fd注册
        self.selector.register(fileobj, events, data)

    def remove_handler(self, fileobj):
        self.selector.unregister(fileobj)

    def run_forever(self):
        self.add_handler(self.pipe[0], selectors.EVENT_READ, self._wake_up)
        while self.alive:
            events = self.selector.select()
            for key, mask in events:
                if key.data:
                    key.data()

    def _wake_up(self):
        os.read(self.pipe[0], 1)

    def stop(self):
        # 简单化的退出逻辑
        self.alive = False
        os.write(self.pipe[1], b'.')


def get_event_loop():
    global running_loop
    if running_loop:
        return running_loop
    running_loop = IOLoop()
    return running_loop


class Future():

    def __init__(self):
        self._result = None
        self._callbacks = []

    def add_done_callback(self, fn):
        self._callbacks.append(fn)

    def set_result(self, result):
        self._result = result
        self._schedule_callbacks()

    def _schedule_callbacks(self):
        callbacks = self._callbacks[:]
        if not callbacks:
            return
        self._callbacks[:] = []
        for callback in callbacks:
            callback()

    def __iter__(self):
        yield self
        return self._result


class Task:
    def __init__(self, coro):
        self.coro = coro
        self._step()

    def _step(self):
        try:
            future = self.coro.send(None)
        except StopIteration:
            return
        future.add_done_callback(self._step)


class Connection():
    def __init__(self, sock):
        self.sock = sock
        self.client = None
        self.io_loop = get_event_loop()

    def accept(self):
        f = Future()

        def on_accept():
            try:
                self.client, addr = self.sock.accept()
                print("connetc from ", addr)
            except BlockingIOError:
                return
            self.io_loop.remove_handler(self.sock)
            f.set_result(None)
        self.io_loop.add_handler(self.sock, selectors.EVENT_READ, on_accept)
        yield from f

    def recv(self):
        f = Future()

        def on_recv():
            self.io_loop.remove_handler(self.client)
            f.set_result(self.client.recv(1024))
        self.io_loop.add_handler(self.client, selectors.EVENT_READ, on_recv)
        response = yield from f
        return response

    def sendall(self, data):
        if self.client:
            self.client.sendall(data)
            self.close_client()

    def close_client(self):
        if self.client:
            self.client.close()
            self.client = None

    def close(self):
        self.sock.close()


class AsyncServer():

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
                worker = AsyncWorker(self.sock)
                Task(worker.run())
                io_loop = get_event_loop()
                io_loop.run_forever()
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


class AsyncWorker():
    def __init__(self, sock):
        self.alive = True
        self._sock = sock
        self.connection = Connection(sock)
        self.io_loop = get_event_loop()
        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, sig, frame):
        self.alive = False
        # 让进程从阻塞状态返回
        self.io_loop.stop()

    def run(self):
        while self.alive:
            yield from self.connection.accept()
            request = yield from self.connection.recv()
            self.connection.sendall(self.handle_request(request))
        self.connection.close()

    def handle_request(self, request):
        # 这里简单的返回
        http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
        return http_response


if __name__ == "__main__":
    server = AsyncServer("localhost", 8000)
    server.serve_forever()
