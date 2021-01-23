# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QMutex
from module.module_base import ModuleBase
from ui import ui
import cfg
import debug


class DataDisplay(QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        ModuleBase.__init__(self)
        self.text = ui.e_recv
        self.ishex = False
        self.data = []
        self.data_buf = []
        self.font_init()
        self.display_encode_init()
        self.find_text_init()
        ui.c_hex_show.stateChanged.connect(self._event_hex_show)
        ui.b_clean_recv.clicked.connect(self._event_clean)
        self.mutex = QMutex()
        self.start()

    def font_init(self):
        self.font = ui.c_display_font
        self.font.setCurrentFont(self.text.currentFont())
        self.font.currentFontChanged.connect(self._event_font)
        self.font_size = ui.c_font_size
        self.font_size.valueChanged.connect(self._event_font_size)
        self.font_size.setValue(int(cfg.get(cfg.DATA_FONT_SIZE, '9')))
        self._event_font_size()

    def display_encode_init(self):
        self.cur_encode = cfg.get(cfg.DISPLAY_ENCODE, 'GB2312')
        table = ['UTF-8', 'GB2312', 'ASCLL', 'ANSI', 'GBK', 'UNICODE', 'GB18030']
        ui.c_display_encode.addItems(table)
        ui.c_display_encode.setCurrentText(self.cur_encode)
        ui.c_display_encode.currentTextChanged.connect(self.change_encode)

    def find_text_init(self):
        ui.b_find_text.clicked.connect(self.highlight_text)
        ui.e_find_data.textChanged.connect(self.highlight_text)

    def highlight_text(self):
        text = ui.e_find_data.displayText()
        ui.highlight_text(self.text, text, 'red')

    def change_encode(self, encode):
        self.cur_encode = encode
        cfg.set(cfg.DISPLAY_ENCODE, encode)
        debug.info('显示编码：' + encode)
        if not self.ishex:
            self.display_to_text()

    def push(self, data):
        pass

    def _event_clean(self):
        self.mutex.lock()
        self.data_buf.clear()
        self.data = []
        self.text.clear()
        ui.set_lcd_recv_len_signal.emit(False, 0)
        self.mutex.unlock()

    def display_to_text(self):
        d = self._data_decode(self.data_buf)
        self.text.clear()
        ui.e_recv_signal.emit(d)
        ui.set_lcd_recv_len_signal.emit(False, len(self.data_buf))
        return True

    def display_to_hex(self):
        d = self._data_to_hex(self.data_buf)
        self.text.clear()
        ui.e_recv_signal.emit(d)
        ui.set_lcd_recv_len_signal.emit(False, len(self.data_buf))
        return True

    def hex_mode(self, ishex):
        '''所有数据进行转换'''
        if ishex:
            self.display_to_hex()
            self.ishex = ishex
        else:
            if not self.display_to_text():
                ui.c_hex_show.setCheckState(0)
            else:
                self.ishex = ishex

    def renew_dispay(self, data):
        self.text.insertPlainText(data)

    def parse(self, data):
        # print(data)
        self.mutex.lock()
        self.data.append(data)
        self.data_buf.append(data)
        self.mutex.unlock()
        # self.text.insertPlainText(data.decode())

    def _event_font_size(self):
        s = self.font_size.value()
        self.text.selectAll()
        self.text.setFontPointSize(s)
        cfg.set(cfg.DATA_FONT_SIZE, str(s))

    def _event_font(self):
        self.text.selectAll()
        self.text.setFont(self.font.currentFont())

    def _event_hex_show(self, state):
        self.hex_mode(state)

    def _data_to_hex(self, data):
        temp = []
        for d in data:
            temp.append(d.hex() + ' ')
            data = ''.join(temp)
        return data

    def _data_decode(self, data):
        temp = bytearray()
        temp_err = bytearray()  # 记录不能编码的字节数
        buf = []
        for d in data:
            temp += d
            try:
                s = temp.decode(self.cur_encode)
                if len(temp_err):
                    buf.append('[::{}]'.format(len(temp_err)))
                    temp_err.clear()
                buf.append(s)
                temp.clear()
            except:
                pass
            if len(temp) == 3:  # 三个字节还是不能解码就丢掉头一个
                temp_err += temp[0:1]
                temp = temp[1:]

        return ''.join(buf)

    def _get_diaplay_data(self):
        if len(self.data) == 0:
            return ''
        self.mutex.lock()
        if self.ishex:
            data = self._data_to_hex(self.data)
        else:
            data = self._data_decode(self.data)
        self.mutex.unlock()
        if data:
            self.data = []
        return data

    def run(self):
        while True:
            data = self._get_diaplay_data()
            if len(data) > 0:
                ui.e_recv_signal.emit(data)
                ui.set_lcd_recv_len_signal.emit(True, len(data))
            self.msleep(20)
