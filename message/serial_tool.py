import serial
from PyQt5 import QtCore
from serial.tools import list_ports
from ui import ui
import debug


class SerialMesssge():
    def __init__(self):
        self._finish = False
        self.serial = serial.Serial(timeout=1)  # 设置1秒超时
        self.cur_port = None
        self.cur_baudrate = '115200'
        self.serial_renew = QtCore.QTimer()
        self.serial_renew.timeout.connect(self._renew_port_list)
        self.serial_renew.start()
        self._init_baudrate_list()
        ui.baudrate.currentIndexChanged.connect(self._event_change_serial_info)
        ui.serial_port.currentIndexChanged.connect(self._event_change_serial_info)

    def port_list(self):
        return [i[0] for i in list(list_ports.comports())]

    def baudrate_list(self):
        return ['1200', '2400', '4800', '9600', '19200', '38400', '115200', '230400', '460800', '921600']

    def status(self):
        return self.serial.is_open

    def close(self):
        self._finish = True
        if self.status():
            self.serial.close()

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
        return self.serial.write(data)

    def _open(self, port, baudrate):
        self.serial.port = port
        self.serial.baudrate = baudrate
        try:
            self.serial.open()
        except:
            debug.info_ln('串口打开失败')

    def _event_change_serial_info(self, idx):
        if self.status():
            self.event_open()

    def event_open(self):
        if self.status():
            self.close()
        port = ui.serial_port.currentText()
        baudrate = ui.baudrate.currentText()
        self._open(port, int(baudrate))
        debug.info_ln('串口 {} {} {}'.format(port, baudrate, self.status()))

    def _init_baudrate_list(self):
        baudrate_list = self.baudrate_list()
        ui.baudrate.addItems(baudrate_list)
        ui.baudrate.setCurrentText(self.cur_baudrate)

    def _is_port_list(self, ports):
        if len(ports) != ui.serial_port.count():
            return True
        for p in ports:
            if ui.serial_port.findText(p) == -1:
                return True
        return False

    def _renew_port_list(self):
        port_list = self.port_list()
        if self._is_port_list(port_list):
            ui.serial_port.clear()
            ui.serial_port.addItems(port_list)
            cur = self.cur_port
            ui.serial_port_signal.emit(port_list, cur)
        self.serial_renew.start(1000)
