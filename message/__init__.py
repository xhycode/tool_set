# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from message import serial_tool
from ui import ui
import debug

CONNRCT_NONE = None
CONNTET_SERIAL = 1
CONNECT_TCP_CLINE = 2


class Message():
    def __init__(self):
        self.serial = serial_tool.SerialMesssge()
        self.cur_connect = self.serial
        self.state = False
        self.auto_send = QtCore.QTimer()
        self.auto_send.timeout.connect(self._event_auto_send_timer)
        self.bind()

    def bind(self):
        ui.b_send.clicked.connect(self._event_send)
        ui.b_open.clicked.connect(self._event_open_serial)
        ui.b_clear_send.clicked.connect(self._event_clean_send)
        ui.b_status_control.clicked.connect(self._event_status_control)
        ui.c_auto_send.stateChanged.connect(self._event_auto_send)        

    def recv_line(self):
        if self.cur_connect.status():
            return self.cur_connect.recv_line()
        return None

    def recv(self, count = 1):
        try:
            if self.cur_connect.status():
                return self.cur_connect.recv(count)
            return None
        except:
            if not self.state:
                return None  # 主动断开不重新打开
            if not self.cur_connect.status():
                self.cur_connect.event_open()
            if not self.cur_connect.status():
                ui.b_status_control.setText('连接断开')
                debug.info_ln('连接被断开')
            return None

    def send(self, data):
        if self.cur_connect.status():
            send_len = self.cur_connect.send(data)
            ui.lcd_send_len.display(send_len + ui.lcd_send_len.intValue())
            print("send len:" + str(send_len))
            return send_len
        return None

    def status(self):
        return self.cur_connect.status()

    def _add_extend_send(self, win):
        pass

    def _event_extend_send(self):
        pass

    def _event_extend_all_select(self):
        pass

    def _event_extend_all_send(self):
        pass

    def _event_send(self):
        if self.cur_connect.status():
            data = ui.e_send.toPlainText()
            if len(data) > 0:
                try:
                    if ui.c_hex_send.checkState():
                        self.send((bytes.fromhex(data)))
                    else:
                        self.send(data.encode())
                except:
                    self.auto_send.stop()
                    debug.info_ln('数据格式错误')
        else:
            debug.info_ln('当前没有连接')

    def _event_status_control(self):
        if self.cur_connect.status():
            self.cur_connect.close()
            ui.b_status_control.setText('未连接')
            self.state = False
        else:
            index = ui.tool_cfg.currentIndex()
            print(index)
            if index == 0:
                self._event_open_serial()
            elif index == 1:
                self._event_tcp_connect()
            self.state = True

    def _event_open_serial(self):
        self.serial.event_open()
        if self.serial.status():
            ui.b_status_control.setText('串口已连接')
            self.state = True
        else:
            ui.b_status_control.setText('串口打开失败')
            self.state = False

    def _event_tcp_connect(self):
        pass

    def _event_clean_send(self):
        ui.lcd_send_len.display(0)
        ui.e_send.clear()

    def _event_clean_recv(self):
        pass

    def _event_hex_send(self):
        pass

    def _event_file(self):
        pass

    def _event_set_cache(self):
        pass

    def _event_auto_send(self):
        print(ui.c_auto_send.checkState())
        if ui.c_auto_send.checkState():
            self.auto_send.start()
        else:
            self.auto_send.stop()

    def _event_auto_send_timer(self):
        self._event_send()
        t = ui.e_auto_send_time.value() * 1000  # ms
        self.auto_send.start(t)