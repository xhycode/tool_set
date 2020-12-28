# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QTimer
from message import serial_tool
from message import tcp_client
from message import tcp_server
from message.protocol import Protocol
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
    ''' 管理不同的消息类型,对外开放统一的接口'''

    def __init__(self):
        super().__init__()
        self.message_module_init()
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

    def message_module_init(self):
        ''' 初始化已有的连接方式 '''
        self.serial = serial_tool.SerialMesssge()
        self.client = tcp_client.TCPClinet()
        self.server = tcp_server.TCPServer()
        # 当前连接设置成上次使用的连接方式，默认是串口连接
        self.connect_mode = cfg.get(cfg.MSG_CONNRET_MODE, CONNTET_SERIAL)
        self.set_connect_mode(self.connect_mode)
        self.state = False  # 连接状态

    def set_connect_mode(self, connect):
        ''' 将当前连接设置到选择的连接方式，并保存到配置文件
        '''
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
        ''' 扩展(快捷)发送区的初始化
            扩展区的所有数据都会保存，初始化会恢复上次的数据
        '''
        self.extend_send_index = 0  # 顺序发送时用到的索引记录
        self.extend_count = 22  # 扩展发送区发送栏的个数
        self.extend_send_info = []  # 列表的每个成员是个发送栏
        for i in range(self.extend_count):
            temp = {}
            # getattr 从类中根据属性的名字字符串获取属性，由于名字有规律，所以用循环方便
            temp['btn'] = getattr(ui, 'b_extend_send_' + str(i + 1))  # 发送的按键
            temp['data'] = getattr(ui, 'e_extend_send_' + str(i + 1))  # 数据栏
            temp['select'] = getattr(ui, 'c_extend_send_' + str(i + 1))  # 选择框
            last_data = cfg.get('extend_data_' + str(i+1))  # 恢复上次关闭时的数据
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
        ''' 底部发送区部件的初始化及发送线程初始化
        '''
        self.send_queue = queue.Queue()  # 存放bytes类型数据
        self.auto_send_mode = AUTO_SEND_NONE
        self.auto_send = QTimer()
        self.auto_send.timeout.connect(self._event_auto_send_timer)
        ui.c_hex_send.setCheckState(int(cfg.get(cfg.HEX_SEND_STATE, '0')))
        ui.e_auto_send_time.setValue(float(cfg.get(cfg.AUTO_SEND_TIME, '1.0')))
        self.send_encode_init()
        self.start()  # 开启发送线程，继承来的，从 run() 函数运行

    def send_encode_init(self):
        ''' 发送可以使用不同的编码格式，
            要正确的选择编码，要不接收端可能解码不了
        '''
        self.cur_encode = cfg.get(cfg.SEND_ENCODE, 'GB2312')
        table = ['UTF-8', 'GB2312', 'ASCLL', 'ANSI', 'GBK', 'UNICODE', 'GB18030']
        ui.c_send_encode.addItems(table)
        ui.c_send_encode.setCurrentText(self.cur_encode)
        ui.c_send_encode.currentTextChanged.connect(self.change_encode)

    def change_encode(self, encode):
        ''' 发送编码更改的事件处理
        '''
        self.cur_encode = encode
        cfg.set(cfg.SEND_ENCODE, encode)
        debug.info('发送编码：' + encode)

    def extend_enter_status_save(self, state):
        ''' 保存扩展发送的换行复选框状态 
            复选框改变事件调用
        '''
        cfg.set(cfg.EXTEND_ENTER_STATE, state)

    def extend_cyclic_status_save(self, state):
        ''' 保存扩展发送的循环发送复选框状态 
            复选框改变事件调用
        '''
        cfg.set(cfg.EXTEND_CYCLIC, state)

    def extend_send_save(self):
        ''' 扩增发送区的数据有变化就全部保存一遍，
            人的输入还是很慢的，所以全都保存没什么影响
        '''
        for i in range(self.extend_count):
            cfg.set('extend_data_' + str(i+1),  # 输入数据的保存
                    self.extend_send_info[i]['data'].displayText())
            cfg.set('extend_selsct_' + str(i+1),  # 选中复选框的状态保存
                    self.extend_send_info[i]['select'].checkState())

    def hex_send_state_save(self, state):
        ''' 保存发送区的十六进制发送复选框状态 
            复选框改变事件调用
        '''
        cfg.set(cfg.HEX_SEND_STATE, str(state))
    
    def auto_send_time_save(self, new_time):
        ''' 保存发送区的十六进制发送复选框状态 
            复选框改变事件调用
        '''
        cfg.set(cfg.AUTO_SEND_TIME, '{:.3f}'.format(new_time))

    def get_next_extend_data(self):
        ''' 循环发送时获取下一个要发送的数据
            没被选中的不发送
        '''
        index = self.extend_send_index
        while True:
            if self.extend_send_info[index]['select'].checkState():
                # 找到下一个被选中的数据
                data = self.extend_send_info[index]['data'].displayText()
                if ui.c_entend_enter.checkState():
                    data += '\n'  # 勾选了自动换行
                self.extend_send_index = index + 1
                return data
            index = (index + 1) % self.extend_count  # 循环累加，到最大会从头开始
            if index == self.extend_send_index:  # 找了一圈没有选中的
                debug.err('没有选中的数据')
                return None
            if index == 0:  # 循环一圈了，要判断是否重新循环
                if not ui.c_extend_cyclic_send.checkState():  # 没勾选循环选项
                    debug.info('顺序发送结束')
                    return None

    def recv_line(self):
        ''' 收到 \n 才会停止接收
        '''
        if self.cur_connect.status():
            return self.cur_connect.recv_line()
        return None

    def recv(self, count=1):
        ''' 接收 count 数据，默认是1个
            连接异常返回 None
        '''
        try:
            if self.cur_connect.status():
                return self.cur_connect.recv(count)
            return None
        except:
            if not self.state:
                return None  # 主动断开不重新打开
            # self.state 没被置位说明意外断开了连接，尝试重新打开一次
            if not self.cur_connect.status():
                self.cur_connect.event_open()
            # 再判断一次打开是否成功
            if not self.cur_connect.status():
                ui.b_status_control.setText('连接断开')
                debug.err('连接被断开')
            return None

    def send(self, data, encode='GB2312', ishex=False, packet=False):
        ''' data ：类型 str
            这个发送不是立即发送，而是放到缓存区等待线程发送
        '''
        try:
            debug.info(data)
            if ishex:
                b_data = bytes.fromhex(data)
            else:
                b_data = data.encode(encode)
        except:
            self.auto_send.stop()
            debug.err('数据格式错误')
            return False
        if packet:
            b_data = Protocol.pack(data=b_data)
            print(b_data)
        self.send_queue.put(b_data)
        if not self.cur_connect.status():
            debug.err('未连接,连接后会继续发送')
        return True

    def status(self):
        return self.cur_connect.status()

    def _event_extend_send(self):
        ''' 扩展发送区的单个发送事件触发
            只发送被按下发送的数据框数据
        '''
        is_packet = ui.c_is_pack.checkState()
        # 因为要循环检测哪个被按下了，所以事件要设置成按下触发
        # 如果设置成弹起触发，则无法分辨谁被按下了
        for extend in self.extend_send_info:
            if extend['btn'].isDown():
                data = extend['data'].displayText()
                if ui.c_entend_enter.checkState():
                    data += '\n'
                print(data)
                self.send(data, self.cur_encode, 0, is_packet)

    def _event_extend_all_select(self, state):
        ''' 扩展区的全选事件
            所有的复选框会与 state 状态同步
        '''
        for extend in self.extend_send_info:
            extend['select'].setCheckState(state)

    def _stop_extend_send(self):
        ''' 停止扩展区的自动发送
        '''
        self.auto_send_mode = AUTO_SEND_NONE
        self.auto_send.stop()
        ui.b_extend_send_all.setText('发送按顺序')

    def _event_extend_all_send(self):
        ''' 扩展发送的顺序发送按钮触发，
            按照顺序将选中的数据一次发出
            如果勾选了循环发送，则会循环的发送直到手动停止
        '''
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
        ''' 发送区的数据发送 '''
        if self.cur_connect.status():
            data = ui.e_send.toPlainText()
            is_packet = ui.c_is_pack.checkState()
            ishex = ui.c_hex_send.checkState()
            ret = self.send(data, self.cur_encode, ishex=ishex, packet=is_packet)
            if not ret:
                debug.err('数据格式错误')
                if ui.c_auto_send.checkState():
                    self._stop_main_auto_send()
        else:
            debug.err('当前没有连接')

    def _event_status_control(self):
        ''' 根据当期的连接模式，控制连接的打开/关闭 
        '''
        if self.cur_connect.status():
            self.cur_connect.close()
            ui.b_status_control.setText('未连接')
            self.state = False
        else:
            # 因为要同步改变显示状态，所以分别调用对应连接的打开比较方便
            if self.connect_mode == CONNTET_SERIAL:
                self._event_open_serial()
            elif self.connect_mode == CONNECT_TCP_CLINET:
                self._event_tcp_client_connect()
            elif self.connect_mode == CONNECT_TCP_SERVER:
                self._event_tcp_client_connect()
            self.state = True

    def _event_open_serial(self):
        ''' 点击串口连接事件
            会断开其他连接
        '''
        if self.connect_mode != CONNTET_SERIAL:
            self.cur_connect.close()
        if not self.serial.status():
            self.serial.event_open()
        else:
            self.serial.close()
        if self.serial.status():
            ui.b_status_control.setText('关闭串口')
            self.state = True
        else:
            ui.b_status_control.setText('打开串口')
            self.state = False
        self.set_connect_mode(CONNTET_SERIAL)

    def _event_tcp_client_connect(self):
        ''' 点击 TCP客户端 连接事件
            只有打开没有关闭功能
            会断开其他连接
        '''
        if self.connect_mode != CONNECT_TCP_CLINET:
            self.cur_connect.close()
        if self.client.status():
            self.client.close()
        else:
            self.client.event_open()
        # 判断打开是否成功,并改变状态
        if self.client.status():
            self.state = True
            ui.b_status_control.setText('断开')
        else:
            self.state = False
            ui.b_status_control.setText('连接')
        self.set_connect_mode(CONNECT_TCP_CLINET)

    def _event_tcp_server_connect(self):
        ''' 点击 TCP服务器 连接事件
            只有打开没有关闭功能
            会断开其他连接
        '''
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
        ''' 清空底部发送区数据 '''
        ui.lcd_send_len.display(0)
        ui.e_send.clear()

    def _stop_main_auto_send(self):
        ''' 停止底部发送区的自动发送 '''
        self.auto_send.stop()
        ui.c_auto_send.setCheckState(False)
        self.auto_send_mode = AUTO_SEND_NONE

    def _event_auto_send(self, state):
        ''' 开始底部发送区的自动发送事件 '''
        if state:
            if self.auto_send_mode == AUTO_SEND_EXTEND:
                self._stop_extend_send()
            self.auto_send.start()
            self.auto_send_mode = AUTO_SEND_MAIN
        else:
            self._stop_main_auto_send()

    def _event_auto_send_timer(self):
        ''' 发送区自动发送和扩展区循环发送的定时器处理函数
            两种模式公用一个发送时间
            每次只有一个模式发送，在各自的触发函数中处理的
        '''
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

            
