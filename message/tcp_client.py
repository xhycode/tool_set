import socket
from ui import ui
import cfg
import debug
import sys
sys.path.append('./')
from message.message_base import MessageBase


class TCPClinet(MessageBase):
    def __init__(self):
        last_ip = cfg.get(cfg.TCP_CLIENT_IP, '127.0.0.1')
        ui.e_tcp_client_ip.setText(last_ip)
        last_port = cfg.get(cfg.TCP_CLIENT_PORT, '8080')
        ui.e_tcp_client_port.setText(last_port)
        socket.setdefaulttimeout(10)
        self.BUFSIZ = 1024
        self.state = False

    def status(self):
        return self.state

    def _save_server_info(self, ip, port):
        cfg.set(cfg.TCP_CLIENT_IP, ip)
        cfg.set(cfg.TCP_CLIENT_PORT, port)

    def _get_server_info(self):
        ip = ui.e_tcp_client_ip.displayText()
        port = ui.e_tcp_client_port.displayText()
        if not self.check_ip(ip):
            debug.err('ip地址格式错误')
            return None
        if not port.isdigit():
            debug.err('端口格式错误')
            return None
        self._save_server_info(ip, port)
        return (ip, int(port))

    def event_open(self):
        if self.state:
            self.close()
        else:
            s_info = self._get_server_info()
            if s_info is None:
                return False
            try:
                self.clinet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(self.clinet_socket.connect(s_info))
                self.state = True
                debug.info('连接服务器成功')
                ui.b_connect_client.setText('断开')
            except:
                self.state = False
                debug.err('连接服务器失败')

    def close(self):
        if self.state:
            self.clinet_socket.close()
            self.state = False
            debug.info("客户端：断开连接")
        ui.b_connect_client.setText('连接')

    def recv(self, count=None):
        if not self.state:
            return None
        try:
            if count:
                data = self.clinet_socket.recv(self.BUFSIZ)
            else:
                data = self.clinet_socket.recv(count)
            return data
        except:
            debug.err('连接断开')
            self.clinet_socket.close()
            self.state = False
            return None

    def send(self, data):
        try:
            return self.clinet_socket.send(data)
        except:
            debug.err('发送失败')
            return 0

    def check_ip(self, ipaddr):
        addr = ipaddr.strip().split('.')
        if len(addr) != 4:
            return False
        for i in range(4):
            if not addr[i].isdigit():
                return False
            if int(addr[i]) > 255 or int(addr[i]) < 0:
                return False
        return True
