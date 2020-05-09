
# -*- coding: utf-8 -*-
from module.module_base import ModuleBase
from ui import ui
from PyQt5.QtCore import QThread
import pyqtgraph as pg
import debug

WAVEFOR_CHN_CNT = 8
PLOT_INDEX = 0
DATA_INDEX = 1
STATU_INDEX = 2
COLOR = ['b', 'g', 'r', 'c', 'm', 'y', 'w', 'k']

class _curve():
    def __init__(self, data_cnt=1000):
        self.data = []
        self.data_cnt = data_cnt
        self.is_show = True

    def clear(self):
        self.data = []

class Waveform(QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        self.plot = ui.g_waveform
        self.plot.addLegend()  # 不添加就显示不了图例 ，一定要放在plot前调用
        self._coordinate_config('y', 'x', 'y/x')
        self.curves = {}
        self.line_data = ''
        ui.c_all_chn.stateChanged.connect(self.test)
        self.start()

    def _coordinate_config(self, lift, bottom, title):
        self.plot.showGrid(x=True, y=True, alpha=0.5)
        self.plot.setLabels(left=lift, bottom=bottom,
                            title=title)  # left纵坐标名 bottom横坐标名
        label = pg.TextItem()
        self.plot.addItem(label)

    def get_frame(self):
        '''获取帧，方便嵌入到其他窗口显示'''
        pass

    def _get_chn_info(self, chn):
        '''获取波形界面,如果没有就添加一个新通道'''
        if not ui.get_curves(chn):
            ui.add_curves(chn)
            self.curves[chn] = _curve()
        return self.curves[chn]

    def run(self):
        while True:
            for chn, curve in self.curves.items():
                if curve.is_show:
                    ui.g_waveform_signal.emit(chn, curve.data)
                else:
                    curve.plot.clear()
            QThread.msleep(20)

    def show(self, chn):
        '''显示对应的通道数据'''
        if self.curves.get(chn):
            self.curves[chn].is_show = True

    def hide(self, chn):
        '''隐藏对应的通道数据'''
        if self.curves.get(chn):
            self.curves[chn].is_show = False

    def append(self, chn, data):
        '''添加一个数据到通道 data是数字'''
        d = self._get_chn_info(chn)
        d.data.append(data)

    def set_data(self, chn, data=[]):
        '''直接赋值数据到对应通道，data是列表'''
        d = self._get_chn_info(chn)
        d.data = data
        ui.g_waveform_signal.emit(chn, d.data)

    def clear(self, chn):
        '''清除对应通道的数据'''
        if self.curves.get(chn):
            self.curves[chn].clear()
            ui.g_waveform_clear_signal.emit(chn)

    def clear_all(self):
        '''清除所有通道的数据'''
        for chn in self.curves.keys():
            self.curves[chn].clear()

    def get(self):
        '''获取通道信息,通道名列表形式 [ch1_name, ch2_name,...]'''
        return list(self.curves.keys())

    def pop(self, chn):
        '''获取通道最后一个数据，不会删除'''
        if self.curves.get(chn):
            return self.curves[chn].data[-1]
        else:
            return None

    def _between_str(self, string, start, end):
        head = string.find(start)
        tail = string.find(end)
        if head >= 0 and tail > 0 and tail > head:
            return string[head + 1: tail]
        else:
            return None

    def parse(self, data):
        ch = data.decode()
        print(ch)
        if ch is '\n':
            print(type(self.line_data))
            debug.info_ln(self.line_data)
            name = self._between_str(self.line_data, '<', '>')
            d = self._between_str(self.line_data, '[', ']')
            if name and d:
                self.append(name, float(d))
            self.line_data = ''
        else:
            self.line_data += ch