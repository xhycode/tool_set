
# -*- coding: utf-8 -*-
import sys
sys.path.append('./')
from module.module_base import ModuleBase
from ui import ui
from PyQt5.QtCore import QThread
import debug


WAVEFOR_CHN_CNT = 8
PLOT_INDEX = 0
DATA_INDEX = 1
STATU_INDEX = 2
COLOR = ['b', 'g', 'r', 'c', 'm', 'y', 'w', 'k']


class _curve():
    def __init__(self, chn_name, chn_num, cache_size=1000):
        self.data = []
        self.cache_size = cache_size
        self.chn_name = chn_name
        self.b_clean = getattr(ui, 'b_chn_clear_' + str(chn_num))
        self.c_chn = getattr(ui, 'c_chn_' + str(chn_num))
        self.c_chn.setCheckState(2)
        self.c_chn.setText(chn_name)

    def clear_data(self):
        self.data = []
        ui.g_waveform_clear_signal.emit(self.chn_name)

    def append(self, data):
        if len(self.data) >= self.cache_size:
            self.data = self.data[1:]
        self.data.append(data)

    def set_cache(self, size):
        self.cache_size = size
        if len(self.data) >= self.cache_size:
            self.data = self.data[self.cache_size - len(self.data):]

    def renew_diaplay(self):
        if self.c_chn.checkState():
            ui.g_waveform_signal.emit(self.chn_name, self.data)
        else:
            ui.g_waveform_clear_signal.emit(self.chn_name)


MAX_CHANNAL_COUNT = 16


class Waveform(QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        self.channal_count = 0
        self.channal_cache = 1000
        self.curves = {}
        self.line_data = ''
        ui.c_chn_all.stateChanged.connect(self.all_show)
        ui.b_chn_clear_all.clicked.connect(self.all_clear)
        self.start()

    def new_chn_num(self):
        if self.channal_count >= MAX_CHANNAL_COUNT:
            return None
        chn_num = self.channal_count
        self.channal_count += 1
        return chn_num

    def _get_chn_info(self, chn):
        '''获取波形界面,如果没有就添加一个新通道'''
        if not ui.get_curves(chn):
            chn_num = self.new_chn_num()
            if chn_num is not None:
                ui.add_curves(chn)
                self.curves[chn] = _curve(chn, chn_num, self.channal_cache)
                # 放到类中子类中不能触发信号，所以放在这里了
                self.curves[chn].b_clean.pressed.connect(self.chn_clear_data)

            else:
                return None
        return self.curves[chn]

    def all_show(self):
        for curve in self.curves.values():
            curve.c_chn.setCheckState(ui.c_chn_all.checkState())

    def append(self, chn, data):
        '''添加一个数据到通道 data是数字'''
        d = self._get_chn_info(chn)
        if d:
            d.append(data)

    def chn_clear_data(self):
        for curve in self.curves.values():
            if curve.b_clean.isDown():
                curve.clear_data()

    def all_clear(self, chn):
        for curve in self.curves.values():
            curve.clear_data()

    def _between_str(self, string, start, end):
        head = string.find(start)
        tail = string.find(end)
        if head >= 0 and tail > 0 and tail > head:
            return string[head + 1: tail]
        else:
            return None

    def parse(self, data):
        ch = data.decode()
        if ch == '\n':
            try:
                debug.info_ln(self.line_data)
                name = self._between_str(self.line_data, '<', '>')
                d = self._between_str(self.line_data, '[', ']')
                if name and d:
                    self.append(name, float(d))
                self.line_data = ''
            except:
                debug.info_ln('数据解析错误')
        else:
            self.line_data += ch

    def run(self):
        while True:
            for curve in self.curves.values():
                curve.renew_diaplay()
            QThread.msleep(20)
