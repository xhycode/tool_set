# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread
from message import Message
from module import ModuleManage


class Control(QThread):  # 继承类
    '''
        控制数据与各个模块间的通信
    '''

    def __init__(self):
        super().__init__()
        self.msg = Message()  # 消息处理
        self.md = ModuleManage()  # 功能模块管理
        self.start()

    def run(self):
        ''' 说明：线程 start 后调用的函数
            功能：接收数据并赋值到各模块
        '''
        while True:
            if not self.msg.status():
                self.msleep(100)
                continue
            data = self.msg.recv()
            if data is not None:
                if len(data) > 0:
                    self.md.parse(data)
            else:
                self.msleep(10)
