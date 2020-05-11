# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from message import serial_tool
from ui import ui
import debug
import cfg

CONNRCT_NONE = None
CONNTET_SERIAL = 1
CONNECT_TCP_CLINE = 2

AUTO_SEND_NONE = 0
AUTO_SEND_MAIN = 1
AUTO_SEND_EXTEND = 2

class Message():
    def __init__(self):
        self.serial = serial_tool.SerialMesssge()
        self.cur_connect = self.serial
        self.state = False
        self.auto_send_mode = AUTO_SEND_NONE
        self.auto_send = QtCore.QTimer()
        self.auto_send.timeout.connect(self._event_auto_send_timer)
        self.bind()
        self.extend_send_init()

    def bind(self):
        ui.b_send.clicked.connect(self._event_send)
        ui.b_open.clicked.connect(self._event_open_serial)
        ui.b_clear_send.clicked.connect(self._event_clean_send)
        ui.b_status_control.clicked.connect(self._event_status_control)
        ui.c_auto_send.stateChanged.connect(self._event_auto_send)
        ui.c_all_exend_send.stateChanged.connect(self._event_extend_all_select)
        ui.b_extend_send_all.clicked.connect(self._event_extend_all_send)

    def extend_send_init(self):
        self.extend_send_index = 0
        self.extend_count = 22
        self.extend_send_info = []
        for i in range(self.extend_count):
            temp = {}
            temp['btn'] = getattr(ui, 'b_extend_send_' + str(i + 1))
            temp['data'] = getattr(ui, 'e_extend_send_' + str(i + 1))
            temp['select'] = getattr(ui, 'c_extend_send_' + str(i + 1))
            last_data = cfg.get('extend_data_' + str(i+1))
            temp['data'].setText(last_data)
            last_select = cfg.get('extend_selsct_' + str(i+1), '0')
            temp['select'].setCheckState(int(last_select))
            temp['btn'].pressed.connect(self._event_extend_send)  # 按键按下未抬起时就发送
            temp['data'].editingFinished.connect(self.extend_send_save)
            temp['select'].stateChanged.connect(self.extend_send_save)
            self.extend_send_info.append(temp)

    def extend_send_save(self):
        print(len(self.extend_send_info))
        for i in range(self.extend_count):
            cfg.set('extend_data_' + str(i+1), self.extend_send_info[i]['data'].displayText())
            cfg.set('extend_selsct_' + str(i+1), self.extend_send_info[i]['select'].checkState())

    def get_next_extend_data(self):
        index = self.extend_send_index
        while True:
            if self.extend_send_info[index]['select'].checkState():
                data = self.extend_send_info[index]['data'].displayText()
                if ui.c_entend_enter.checkState():
                    data += '\n'
                self.extend_send_index = index + 1
                return data.encode()
            index = (index + 1) % self.extend_count
            if index == self.extend_send_index:
                debug.info_ln('没有选中的数据')
                return None
            if index == 0:
                if not ui.c_extend_cyclic_send.checkState():
                    debug.info_ln('顺序发送结束')
                    return None

        while index < self.extend_count:
            if self.extend_send_info[index]['select'].checkState():
                data = self.extend_send_info[index]['data'].displayText()
                if ui.c_entend_enter.checkState():
                    data += '\n'
                self.extend_send_index = index + 1
                return data.encode()
            index =  index + 1
        if self.extend_send_index == 0:
            return None  # 没有选中的项
        return None

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
        '''data 是 bytes 类型'''
        if self.cur_connect.status():
            send_len = self.cur_connect.send(data)
            ui.lcd_send_len.display(send_len + ui.lcd_send_len.intValue())
            print("send len:" + str(send_len))
            return send_len
        else:
            debug.info_ln('当前没有连接')
        return None

    def status(self):
        return self.cur_connect.status()

    def _event_extend_send(self):
        print('extend send')
        for extend in self.extend_send_info:
            if extend['btn'].isDown():
                data = extend['data'].displayText()
                if ui.c_entend_enter.checkState():
                    data += '\n'
                print(data)
                self.send(data.encode())

    def _event_extend_all_select(self):
        state = ui.c_all_exend_send.checkState()
        for extend in self.extend_send_info:
            extend['select'].setCheckState(state)

    def _stop_extend_send(self):
        self.auto_send_mode = AUTO_SEND_NONE
        self.auto_send.stop()
        ui.b_extend_send_all.setText('发送按顺序')
        

    def _event_extend_all_send(self):
        if self.auto_send_mode == AUTO_SEND_MAIN:
            self._stop_main_auto_send()
        if self.auto_send_mode == AUTO_SEND_EXTEND:
            self._stop_extend_send()
        else:
            if not self.cur_connect.status():
                debug.info_ln('当前没有连接')
            else:
                self.auto_send_mode = AUTO_SEND_EXTEND
                self.extend_send_index = 0
                ui.b_extend_send_all.setText('停止发送')
                self.auto_send.start()

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

    def _stop_main_auto_send(self):
        self.auto_send.stop()
        ui.c_auto_send.setCheckState(False)
        self.auto_send_mode = AUTO_SEND_NONE

    def _event_auto_send(self):
        if ui.c_auto_send.checkState():
            if self.auto_send_mode == AUTO_SEND_EXTEND:
                self._stop_extend_send()
            self.auto_send.start()
            self.auto_send_mode = AUTO_SEND_MAIN
        else:
           self._stop_main_auto_send()

    def _event_auto_send_timer(self):
        t = ui.e_auto_send_time.value() * 1000  # ms
        if self.auto_send_mode == AUTO_SEND_MAIN:
            self._event_send()
            self.auto_send.start(t)
        else:
            data = self.get_next_extend_data()
            if data is None:
                self._stop_extend_send()
            else:
                self.send(data)
                self.auto_send.start(t)
