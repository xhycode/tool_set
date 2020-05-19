# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread
from message import serial_tool
from message import tcp_client
from message import tcp_server
from ui import ui
import debug
import cfg
import queue

CONNTET_SERIAL = '0'
CONNECT_TCP_CLINET = '1'
CONNECT_TCP_SERVER = '2'

AUTO_SEND_NONE = '0'
AUTO_SEND_MAIN = '1'
AUTO_SEND_EXTEND = '2'


class Message(QThread):
    def __init__(self):
        super().__init__()
        self.connect_init()
        self.send_init()
        self.extend_send_init()
        self.bind()

    def bind(self):
        ui.b_send.clicked.connect(self._event_send)
        ui.b_open_serial.clicked.connect(self._event_open_serial)
        ui.b_connect_client.clicked.connect(self._event_tcp_client_connect)
        ui.b_connect_server.clicked.connect(self._event_tcp_server_connect)
        ui.b_clear_send.clicked.connect(self._event_clean_send)
        ui.b_status_control.clicked.connect(self._event_status_control)
        ui.c_auto_send.stateChanged.connect(self._event_auto_send)
        ui.c_all_exend_send.stateChanged.connect(self._event_extend_all_select)
        ui.c_entend_enter.stateChanged.connect(self.extend_enter_status_save)
        ui.c_extend_cyclic_send.stateChanged.connect(self.extend_cyclic_status_save)
        ui.b_extend_send_all.clicked.connect(self._event_extend_all_send)
        ui.e_auto_send_time.valueChanged.connect(self.auto_send_time_save)
        ui.c_hex_send.stateChanged.connect(self.hex_send_state_save)

    def connect_init(self):
        self.serial = serial_tool.SerialMesssge()
        self.client = tcp_client.TCPClinet()
        self.server = tcp_server.TCPServer()
        self.connect_mode = cfg.get(cfg.MSG_CONNRET_MODE, CONNTET_SERIAL)
        self.set_connect_mode(self.connect_mode)
        self.state = False  # 连接状态

    def set_connect_mode(self, connect):
        self.connect_mode = connect
        if connect == CONNTET_SERIAL:
            self.cur_connect = self.serial
            ui.t_connect_type.setText('串口')
        elif connect == CONNECT_TCP_CLINET:
            self.cur_connect = self.client
            ui.t_connect_type.setText('TCP客户端')
        elif connect == CONNECT_TCP_SERVER:
            self.cur_connect = self.server
            ui.t_connect_type.setText('TCP服务器')
        cfg.set(cfg.MSG_CONNRET_MODE, self.connect_mode)

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
        ui.c_entend_enter.setCheckState(int(cfg.get(cfg.EXTEND_ENTER_STATE, '0')))
        ui.c_extend_cyclic_send.setCheckState(int(cfg.get(cfg.EXTEND_CYCLIC, '0')))

    def send_init(self):
        self.send_queue = queue.Queue()  # 存放bytes类型数据
        self.auto_send_mode = AUTO_SEND_NONE
        self.auto_send = QtCore.QTimer()
        self.auto_send.timeout.connect(self._event_auto_send_timer)
        ui.c_hex_send.setCheckState(int(cfg.get(cfg.HEX_SEND_STATE, '0')))
        ui.e_auto_send_time.setValue(float(cfg.get(cfg.AUTO_SELD_TIME, '1.0')))
        self.send_encode_init()
        self.start()  # 开启发送线程

    def send_encode_init(self):
        self.cur_encode = cfg.get(cfg.SEND_ENCODE, 'GB2312')
        table = ['UTF-8', 'GB2312', 'ASCLL', 'ANSI', 'GBK', 'UNICODE', 'GB18030']
        ui.c_send_encode.addItems(table)
        ui.c_send_encode.setCurrentText(self.cur_encode)
        ui.c_send_encode.currentTextChanged.connect(self.change_encode)

    def change_encode(self, encode):
        self.cur_encode = encode
        cfg.set(cfg.SEND_ENCODE, encode)
        debug.info('发送编码：' + encode)

    def extend_enter_status_save(self, state):
        cfg.set(cfg.EXTEND_ENTER_STATE, state)

    def extend_cyclic_status_save(self, state):
        cfg.set(cfg.EXTEND_CYCLIC, state)

    def extend_send_save(self):
        for i in range(self.extend_count):
            cfg.set('extend_data_' + str(i+1),
                    self.extend_send_info[i]['data'].displayText())
            cfg.set('extend_selsct_' + str(i+1),
                    self.extend_send_info[i]['select'].checkState())

    def hex_send_state_save(self, state):
        cfg.set(cfg.HEX_SEND_STATE, str(state))
    
    def auto_send_time_save(self, new_time):
        cfg.set(cfg.AUTO_SELD_TIME, '{:.3f}'.format(new_time))

    def get_next_extend_data(self):
        index = self.extend_send_index
        while True:
            if self.extend_send_info[index]['select'].checkState():
                data = self.extend_send_info[index]['data'].displayText()
                if ui.c_entend_enter.checkState():
                    data += '\n'
                self.extend_send_index = index + 1
                return data
            index = (index + 1) % self.extend_count
            if index == self.extend_send_index:
                debug.err('没有选中的数据')
                return None
            if index == 0:
                if not ui.c_extend_cyclic_send.checkState():
                    debug.info('顺序发送结束')
                    return None

    def recv_line(self):
        if self.cur_connect.status():
            return self.cur_connect.recv_line()
        return None

    def recv(self, count=1):
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
                debug.err('连接被断开')
            return None

    def send(self, data, encode='GB2312', ishex=False):
        try:
            if ishex:
                b_data = bytes.fromhex(data)
            else:
                b_data = data.encode(encode)
        except:
            self.auto_send.stop()
            debug.err('数据格式错误')
            return False
        self.send_queue.put(b_data)
        if not self.cur_connect.status():
            debug.err('未连接,连接后会继续发送')
        return True

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
                self.send(data, self.cur_encode, 0)

    def _event_extend_all_select(self, state):
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
                debug.err('当前没有连接')
            else:
                self.auto_send_mode = AUTO_SEND_EXTEND
                self.extend_send_index = 0
                ui.b_extend_send_all.setText('停止发送')
                self.auto_send.start()

    def _event_send(self):
        if self.cur_connect.status():
            data = ui.e_send.toPlainText()
            if ui.c_hex_send.checkState():
                ret = self.send(data, self.cur_encode, ishex=True)
            else:
                ret = self.send(data, self.cur_encode, ishex=False)
            if not ret:
                debug.err('数据格式错误')
                if ui.c_auto_send.checkState():
                    self._stop_main_auto_send()
        else:
            debug.err('当前没有连接')

    def _event_status_control(self):
        if self.cur_connect.status():
            self.cur_connect.close()
            ui.b_status_control.setText('未连接')
            self.state = False
        else:
            if self.connect_mode == CONNTET_SERIAL:
                self._event_open_serial()
            elif self.connect_mode == CONNECT_TCP_CLINET:
                self._event_tcp_client_connect()
            elif self.connect_mode == CONNECT_TCP_SERVER:
                self._event_tcp_client_connect()
            self.state = True

    def _event_open_serial(self):
        if self.connect_mode != CONNTET_SERIAL:
            self.cur_connect.close()
        self.serial.event_open()
        if self.serial.status():
            ui.b_status_control.setText('串口已连接')
            self.state = True
        else:
            ui.b_status_control.setText('串口打开失败')
            self.state = False
        self.set_connect_mode(CONNTET_SERIAL)

    def _event_tcp_client_connect(self):
        if self.connect_mode != CONNECT_TCP_CLINET:
            self.cur_connect.close()
        self.client.event_open()
        if self.client.status():
            ui.b_status_control.setText('断开连接')
            self.state = True
        else:
            ui.b_status_control.setText('连接服务器失败')
            self.state = False
        self.set_connect_mode(CONNECT_TCP_CLINET)

    def _event_tcp_server_connect(self):
        if self.connect_mode != CONNECT_TCP_SERVER:
            self.cur_connect.close()
        self.server.event_open()
        if self.server.status():
            ui.b_status_control.setText('关闭服务器')
            self.state = True
        else:
            ui.b_status_control.setText('服务器启动失败')
            self.state = False
        self.set_connect_mode(CONNECT_TCP_SERVER)

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

    def _event_auto_send(self, state):
        if state:
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
                return
            if self.send(data, self.cur_encode, ishex=False):
                self.auto_send.start(t)
            else:
                self._stop_extend_send()

    def run(self):
        ''' 线程用于发送队列的数据 '''
        while True:
            if self.send_queue.empty() or not self.cur_connect.status():
                self.msleep(20)
                continue
            try:
                data = self.send_queue.get()
                send_len = self.cur_connect.send(data)
                ui.lcd_send_len.display(send_len + ui.lcd_send_len.intValue())
            except:
                debug.err('发送失败')

            
