最近想写个脚本来实现网段扫描，判断有哪些ip在用，最简单的就是将子网内的ip ping个遍。网上找了下貌似python都是通过调用系统来实现ping，在需ping的ip数量多的时候效率太低，自己写又重复造轮子。在网上找到了个ping的代码:
https://github.com/samuel/python-ping/blob/master/ping.py
这代码通过socket发送icmp包，通过select来获取reply，但代码是在python2上运行的，需将print和xrange之类的全改成python3的。
但改完后还是报错，首先报错的是这里
```
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    bytesInDouble = struct.calcsize("d")
    data = (192 - bytesInDouble) * "Q"
    data = struct.pack("d", default_timer()) + data
    my_checksum = checksum(header + data)
```
struct后的header是byte，但却将字符串和byte相加了，考虑到data是icmp的内容，直接改为b’Q‘即可。
接下来报错的是ord函数
```
def checksum(source_string):
    """
    I'm not too confident that this is right but testing seems
    to suggest that it gives the same answers as in_cksum in ping.c
    """
    sum = 0
    countTo = (len(source_string)/2)*2
    count = 0
    while count<countTo:
        thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff # Necessary?
        count = count + 2

    if countTo<len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff # Necessary?

    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff

    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer
```
source_string是byte，校验和也算的不对
修改校验和过程后，能正常ping了，必须用超管权限运行