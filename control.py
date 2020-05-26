# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread
from message import Message
from module import ModuleManage


class ControlThread(QThread):
    def __init__(self, target):
        super().__init__()
        self.target = target

    def run(self):
        self.target()


class Control():  # 继承类
    '''
        控制数据与各个模块间的通信
    '''

    def __init__(self):
        self.msg = Message()  # 消息处理
        self.md = ModuleManage()  # 功能模块管理
        self.recv_init()
        self.send_init()

    def send_init(self):
        self.send_thread = ControlThread(self.send)
        self.send_thread.start()

    def recv_init(self):
        self.recv_thread = ControlThread(self.recv)
        self.recv_thread.start()

    def recv(self):
        ''' 说明：线程 start 后调用的函数
            功能：接收数据并赋值到各模块
        '''
        while True:
            if not self.msg.status():
                QThread.msleep(100)
                continue
            data = self.msg.recv()
            if data is not None:
                if len(data) > 0:
                    self.md.parse(data)
            else:
                QThread.msleep(10)

    def send(self):
        ''' 将模块要发送的数据转发出去 '''
        while(True):
            data = self.md.send_pop()
            if data:
                self.msg.send(data)
            else:
                QThread.msleep(20)
