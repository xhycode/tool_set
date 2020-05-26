# -*- coding: utf-8 -*-
import queue


class ModuleBase():
    ''' 模块的类都要继承这个类,并且要调用父类的__init__()
    '''
    def __init__(self, buf_size=0):
        self.send_queue = queue.Queue(buf_size)

    def parse(self, data):
        ''' 解析传入的数据
            data类型： 一个字节的 bytes
        '''
        pass

    def send_push(self, data):
        ''' 模块发送数据的接口，不需要重构 '''
        if self.send_queue.full():
            return False
        else:
            self.send_queue.put(data)
            return True

    def send_pop(self):
        ''' 获取待发送的数据，给其他模块调用，帮助把这个包里模块的数据发出去
            不需要重构
        '''
        if self.send_queue.empty():
            return None
        else:
            return self.send_queue.get()


if __name__ == "__main__":
    module = ModuleBase()
    module.send_push("G28\n")
    module.send_push("G29\n")
    print(module.send_pop())
    print(module.send_pop())
