import socket
import concurrent.futures as futures
from PyQt5.QtCore import QThread
from ui import ui
import debug
import sys
sys.path.append('./')
from message.message_base import MessageBase
import cfg

STATUE_NONE = 0
STATUE_WAIT = 1
STATUE_CONNECT = 2

class TCPServer(QThread, MessageBase):
    def __init__(self):
        super().__init__()
        self.local_ip_init()
        self.default_port_init()
        self.service = socket.socket()
        self.service.settimeout(None)
        self.statue = STATUE_NONE
        self.start()

    def event_open(self):
        port = ui.e_local_port.displayText()
        if port.isdigit():
            self.ADDRESS = (self.local_ip, int(port))
            self.service.bind(self.ADDRESS)
            self.service.listen(1)  # 只接入一个
            self.statue = True
            cfg.set(cfg.SERVER_PORT, port)

    def get_host_ip(self):
        """查询本机ip地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def local_ip_init(self):
        self.local_ip = self.get_host_ip()
        ui.e_local_ipaddr.setText(self.local_ip)

    def default_port_init(self):
        port = cfg.get(cfg.SERVER_PORT, '8080')
        ui.e_local_port.setText(port)

    def wait_connect(self):
        while True:
            if self.statue == STATUE_WAIT:
                try:
                    debug.info('等待客户端连接')
                    print(self.service.gettimeout())
                    self.sock, addr = self.service.accept()
                    self.sock.settimeout(None)
                    debug.info('客户端已连接:{}'.format(addr))
                    self.statue = STATUE_CONNECT
                    print(self.sock.gettimeout())
                    break
                except:
                    self.msleep(20)
            else:
                self.msleep(20)

    def recv_process(self):
        while self.statue == STATUE_CONNECT:
            d = self.sock.recv(1)
            print(d)
            if len(d) == 0:
                self.close()
                self.statue = STATUE_WAIT

    def run(self):
        while True:
            self.wait_connect()

    def status(self):
        return self.statue != STATUE_NONE

    def close(self):
        if self.statue:
            self.sock.close()
            self.statue = STATUE_NONE
            debug.info("客户端连接断开")

    def recv(self, count=1):
        d = self.sock.recv(count)
        if len(d) == 0:
            self.close()
            self.statue = STATUE_WAIT
            return None
        return d

    def recv_line(self):
        return None

    def send(self, data):
        if self.statue == STATUE_CONNECT:
            return self.sock.send(data)
        return None
