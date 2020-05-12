# -*- coding: utf-8 -*-


class MessageBase():
    def __init__(self):
        pass

    def status(self):
        # 连接状态
        return 0

    def close(self):
        pass

    def recv(self, count=None):
        # count==None 代表全部接受，如果设置数字就接收指定长度
        return None

    def recv_line(self):
        return None

    def send(self, data):
        pass

    def event_open(self):
        pass
