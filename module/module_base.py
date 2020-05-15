# -*- coding: utf-8 -*-
import queue


class ModuleBase():
    def __init__(self, buf_size=0):
        self.send_queue = queue.Queue(buf_size)

    def parse(self, data):
        pass

    def send_push(self, data):
        if self.send_queue.full():
            return False
        else:
            self.send_queue.put(data)
            return True

    def send_pop(self):
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
