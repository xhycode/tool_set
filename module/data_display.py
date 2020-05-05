# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from module.module_base import ModuleBase
from ui import ui


class DataDisplay(QtCore.QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        self.text = ui.e_recv
        self.font = ui.c_display_font
        self.ishex = False
        self.data = []
        self.data_buf = bytes()
        self.font.setCurrentFont(self.text.currentFont())
        self.font_size = ui.c_font_size
        self.font_size.valueChanged.connect(self._event_font_size)
        self.font_size.setValue(self.text.fontPointSize())
        ui.c_hex_show.stateChanged.connect(self._event_hex_show)
        ui.b_clean_recv.clicked.connect(self._event_clean)
        self.mutex = QtCore.QMutex()
        self.start()

    def push(self, data):
        pass

    def _event_clean(self):
        self.mutex.lock()
        self.data_buf = bytes()
        self.data = []
        self.text.clear()
        ui.lcd_recv_len.display(0)
        self.mutex.unlock()

    def hex_mode(self, ishex):
        '''第一次切换时候调用'''
        self.ishex = ishex
        self.text.clear()
        if ishex:
            d = ''.join(['%02x ' % b for b in self.data_buf])
            ui.e_recv_signal.emit(d)
        else:
            ui.e_recv_signal.emit(self.data_buf.decode())

    def renew_dispay(self, data):
        self.text.insertPlainText(data)

    def parse(self, data):
        # print(data)
        self.mutex.lock()
        self.data.append(data)
        self.data_buf += data
        self.mutex.unlock()
        # self.text.insertPlainText(data.decode())

    def _event_font_size(self):
        s = self.font_size.value()
        self.text.selectAll()
        self.text.setFontPointSize(s)

    def _event_hex_show(self):
        self.hex_mode(ui.c_hex_show.checkState())

    def run(self):
        while True:
            temp = []
            if len(self.data) > 0:
                self.mutex.lock()
                for d in self.data:
                    if self.ishex:
                        temp.append(d.hex() + ' ')
                    else:
                        temp.append(d.decode())
                data = ''.join(temp)
                ui.e_recv_signal.emit(data)
                ui.lcd_recv_len.display(ui.lcd_recv_len.value() + len(self.data))
                self.data = []
                self.mutex.unlock()
            self.msleep(10)

