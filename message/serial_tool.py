from serial import Serial
from PyQt5.QtCore import QTimer
from serial.tools import list_ports
from ui import ui
import debug
import cfg
import sys
sys.path.append('./')
from message.message_base import MessageBase


class SerialMesssge(MessageBase):
    def __init__(self):
        self.serial = Serial(timeout=1)  # 设置1秒超时
        self.open_status = False
        self.last_ports = []
        self.is_reopen = False
        self.cur_port = cfg.get(cfg.SERIAL_PORT, 'None')
        self.cur_baudrate = cfg.get(cfg.SERIAL_BAUDRATE, '115200')
        self.serial_renew = QTimer()
        self.serial_renew.timeout.connect(self._renew_port_list)
        self.serial_renew.start()
        self._init_baudrate_list()
        ui.baudrate.currentIndexChanged.connect(self._event_change_serial_info)
        ui.serial_port.currentIndexChanged.connect(self._event_change_serial_info)

    def port_list(self):
        return [i[0] for i in list(list_ports.comports())]

    def baudrate_list(self):
        return ['1200', '2400', '4800', '9600', '19200', '38400', '115200', '230400', '250000', '460800', '921600']

    def status(self):
        return self.serial.is_open

    def close(self):
        if self.status():
            self.serial.close()
        self.open_status = False
        ui.b_open_serial.setText('打开')
        debug.info('串口断开连接')
        

    def recv(self, count=None):
        if not self.status():
            return None
        if count:
            return self.serial.read(count)
        else:
            return self.serial.read_all()

    def recv_line(self):
        return self.serial.read_until()

    def send(self, data):
        try:
            return self.serial.write(data)
        except:
            debug.err('发送失败,串口未连接')
            return 0

    def _open(self, port, baudrate):
        self.serial.port = port
        self.serial.baudrate = baudrate
        self.cur_port = port
        self.open_status = True
        try:
            self.serial.open()
            ui.b_open_serial.setText('关闭')
        except:
            debug.err('串口打开失败')

    def _event_change_serial_info(self, idx):
        ''' 串口或波特率改变了都会重新打开串口 '''
        if self.open_status and ui.serial_port.currentText() != '':
            isport = ui.serial_port.currentText() != self.cur_port  # 串口
            isbaudrate = ui.baudrate.currentText() != self.cur_baudrate
            isonline = self.cur_port in self.port_list()
            # 串口或波特率被手动改变则重新打开, 
            # 如果当前端口不在了, 则是设备不在了,不重新连接
            if (isport or isbaudrate) and isonline:
                self.event_open()

    def event_open(self):
        if self.status():
            self.serial.close()
        port = ui.serial_port.currentText()
        baudrate = ui.baudrate.currentText()
        self._open(port, int(baudrate))
        cfg.set(cfg.SERIAL_PORT, port)
        cfg.set(cfg.SERIAL_BAUDRATE, baudrate)
        debug.info('串口 {} {} {}'.format(port, baudrate, self.status()))

    def _init_baudrate_list(self):
        baudrate_list = self.baudrate_list()
        ui.baudrate.addItems(baudrate_list)
        ui.baudrate.setCurrentText(self.cur_baudrate)

    def _is_port_list(self, ports):
        # # 串口数量变化了就刷新
        if len(ports) != len(self.last_ports):
            return True
        # 有新的串口加入也刷新界面
        for p in ports:
            if ui.serial_port.findText(p) == -1:
                return True
        return False  # 没有变化不刷新

    def _renew_port_list(self):
        ''' 在定时器中刷新串口列表 '''
        port_list = self.port_list()
        if self._is_port_list(port_list):
            self.last_ports = port_list
            debug.info(port_list)
            ui.serial_port_signal.emit(port_list, self.cur_port)
            if self.open_status:
                if self.cur_port in port_list:
                    if self.is_reopen:
                        try:
                            self.is_reopen = False
                            self.serial.close()
                            self.serial.open()
                            ui.b_open_serial.setText('关闭')
                            debug.info('已经重新打开串口')
                        except:
                            debug.err('串口重新打开失败')
                else:
                    self.is_reopen = True
                    debug.err("串口丢失")
        self.serial_renew.start(200)

