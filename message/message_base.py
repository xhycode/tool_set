# -*- coding: utf-8 -*-


class MessageBase():
    ''' 这个包内的模块都要继承这个类
        重构方法时不能改变返回类型
    '''
    def __init__(self):
        pass

    def status(self):
        ''' 返回 bool 类型 '''
        # 连接状态
        return False

    def close(self):
        pass

    def recv(self, count=None):
        ''' count==None 代表全部接受，如果设置数字就接收指定长度
            连接异常返回 None
            正常连接返回 bytes
        '''

        return None

    def recv_line(self):
        '''
            连接异常返回 None
            正常连接返回 bytes
        '''
        return None

    def send(self, data):
        '''  data类型 ：bytes '''
        pass

    def event_open(self):
        ''' 只负责打开 '''
        pass
