import socket
from concurrent.futures import ThreadPoolExecutor


def send():
    short_message = "hello, this is message"
    connect = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    connect.connect(("localhost", 8000))
    connect.sendall(short_message.encode("UTF-8"))
    print(connect.recv(1024))


if __name__ == "__main__":
    executor = ThreadPoolExecutor(10)
    for i in range(20):
        executor.submit(send)
    executor.shutdown(wait=True)
