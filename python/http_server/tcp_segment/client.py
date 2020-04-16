import socket


def send():
    short_message = "hello, this is message"
    another_short_message = "1"
    long_message = """1222222222222222222222222111111111111111111eqwedf1111111111111111111111
    111111dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
    ddddddddddddddddddddddddddddddddddddddddddddddddddddeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeffffffffff
    fffffffffffffffffffffffffffffffffffffffffffffffffffg"""
    long_message = long_message*3 + "end"
    connect = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    connect.connect(("localhost", 8000))
    # B
    connect.sendall(long_message.encode("UTF-8"))
    connect.sendall(another_short_message.encode("UTF-8"))
    # C
    connect.sendall(another_short_message.encode("UTF-8"))
    connect.sendall(long_message.encode("UTF-8"))
    # D
    # connect.sendall(another_short_message.encode("UTF-8"))
    # connect.sendall(short_message.encode("UTF-8"))
    connect.close()


if __name__ == "__main__":
    send()
