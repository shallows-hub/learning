import socket
import asyncio
from asyncio import Future
from typing import (
    Awaitable,
)


class IOStream():
    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket
        self.socket.setblocking(False)
        self.io_loop = asyncio.get_event_loop()

    def connect(self, address: tuple) -> None:
        future = Future()
        try:
            self.socket.connect(address)
        except BlockingIOError:
            pass

        def _handle_connect():
            self.io_loop.remove_writer(self.socket)
            future.set_result(None)
        self.io_loop.add_writer(self.socket, _handle_connect)
        return future

    def write(self, data: bytes) -> None:
        future = Future()

        def _handle_write():
            self.io_loop.remove_writer(self.socket)
            # 正常流程里，这里是要根据缓冲区大小来陆续send的，本对象只是模拟协程的工作，所以不处理细节
            self.socket.sendall(data)
            future.set_result(None)
        self.io_loop.add_writer(self.socket, _handle_write)
        return future

    def read_bytes(self, num_bytes: int) -> Awaitable[bytes]:
        future = Future()

        def _handle_read():
            self.io_loop.remove_reader(self.socket)
            data = self.socket.recv(num_bytes)
            future.set_result(data)
        self.io_loop.add_reader(self.socket, _handle_read)
        return future

    def close(self) -> None:
        if self.socket:
            self.socket.close()
        self.socket = None


if __name__ == '__main__':
    async def main():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        stream = IOStream(s)
        await stream.connect(("localhost", 8000))
        await stream.write(b"GET / HTTP/1.0\r\nHost: localhost\r\n\r\n")
        body_data = await stream.read_bytes(1024)
        print(body_data)
        stream.close()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([main(), main()]))