import socket
import concurrent.futures as futures
from PyQt5.QtCore import QThread
from ui import ui
import debug
import sys
sys.path.append('./')
from message.message_base import MessageBase


class TCPServer(QThread, MessageBase):
    def __init__(self):
        super().__init__()
        self.local_ip = self.get_host_ip()
        ui.e_local_ipaddr.setText(self.local_ip)
        self.start()

    def event_open(self):
        port = ui.e_local_port.displayText()
        if port.isdigit():
            self.ADDRESS = (self.local_ip, port)
            self.clients = []
            self.ex = futures.ThreadPoolExecutor(max_workers=3)
            self.tcpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcpServerSocket.bind(self.ADDRESS)
            debug.info("Server start, listen port{}...".format(self.ADDRESS))
            self.tcpServerSocket.listen(5)

    def get_host_ip(self):
        """查询本机ip地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def run(self):
        pass
