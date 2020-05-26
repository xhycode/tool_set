
# -*- coding: utf-8 -*-
import sys
import time
sys.path.append('./')
from module.module_base import ModuleBase
from ui import ui
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QMutex
from PyQt5.QtWidgets import QFileDialog
import debug
import cfg
from cache import Cache


WAVEFOR_CHN_CNT = 8
PLOT_INDEX = 0
DATA_INDEX = 1
STATU_INDEX = 2
COLOR = ['b', 'g', 'r', 'c', 'm', 'y', 'w', 'k']


class _curve():
    ''' 每个 _curve 类管理一个曲线通道  '''
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
            self.data = self.data[len(self.data) - self.cache_size:]

    def renew_diaplay(self):
        if self.c_chn.checkState():
            ui.g_waveform_signal.emit(self.chn_name, self.data)
        else:
            ui.g_waveform_clear_signal.emit(self.chn_name)


MAX_CHANNAL_COUNT = 16
CACHE_FILE = 'waveform'


class Waveform(QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        ModuleBase.__init__(self)
        self.channal_count = 0
        self.channal_cache = int(cfg.get(cfg.WAVEFORM_CACHE, '1000'))
        ui.e_chn_cache.setText(str(self.channal_cache))
        ui.e_chn_cache.textChanged.connect(self.set_cache_size)
        self.curves = {}
        self.line_data = ''
        self.data_cache_init()
        self.data_lock = QMutex()
        ui.c_chn_all.stateChanged.connect(self.all_show)
        ui.b_chn_clear_all.clicked.connect(self.all_clear)
        self.start()  # 继承的 QThread， 用来刷新数据显示

    def data_cache_init(self):
        self.data_cache = []
        self.cache = Cache('.', CACHE_FILE, clear=True)
        self.write_cache_timer = QTimer()
        self.write_cache_timer.timeout.connect(self.data_write_cache)
        ui.b_save_waveform_data.clicked.connect(self.data_save)
        ui.b_open_waveform_file.clicked.connect(self.open_data)
        self.write_cache_timer.start(5000)
        
    def data_save(self):
        self.data_write_cache()
        filename=QFileDialog.getSaveFileName(ui)
        lines = self.cache.readlines()
        with open(filename[0], 'w') as f:
            f.writelines(lines)
    
    def open_data(self):
        filename=QFileDialog.getOpenFileName(ui)
        self.all_clear()
        with open(filename[0], 'r') as f:
            lines = f.readlines()
            for line in lines:
                try:
                    data = line.split(' ')
                    self.append(data[0], float(data[1]))
                except:
                    debug.err(line)

    def data_write_cache(self):
        self.cache.write_lines(self.data_cache)
        self.data_cache = []

    def set_cache_size(self, text):
        if text.isdigit():
            self.channal_cache = int(text)
            for curve in self.curves.values():
                curve.set_cache(self.channal_cache)
            cfg.set(cfg.WAVEFORM_CACHE, text)
        else:
            ui.e_chn_cache.setText(str(self.channal_cache))
            debug.err('缓存只能设置正整数')

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
                self.data_lock.lock()
                ui.add_curves(chn)
                self.curves[chn] = _curve(chn, chn_num, self.channal_cache)
                # 放到类中子类中不能触发信号，所以放在这里了
                self.curves[chn].b_clean.pressed.connect(self.chn_clear_data)
                self.data_lock.unlock()
            else:
                return None
        return self.curves[chn]

    def all_show(self, state):
        for curve in self.curves.values():
            curve.c_chn.setCheckState(state)

    def append(self, chn, data):
        '''添加一个数据到通道 data是数字'''
        d = self._get_chn_info(chn)
        if d:
            d.append(data)

    def chn_clear_data(self):
        for curve in self.curves.values():
            if curve.b_clean.isDown():
                curve.clear_data()

    def all_clear(self):
        for curve in self.curves.values():
            curve.clear_data()

    def _between_str(self, string, start, end):
        head = string.find(start)
        tail = string.find(end)
        if head >= 0 and tail > 0 and tail > head:
            return string[head + 1: tail]
        else:
            return None

    def cut_time_str(self):
        t = time.localtime()
        ms = int(time.time() * 100 % 100)
        return "{}.{}.{}.{}.{}.{}.{}".format(t.tm_year,
                                          t.tm_mon,
                                          t.tm_mday,
                                          t.tm_hour,
                                          t.tm_min,
                                          t.tm_sec,
                                          ms)

    def parse(self, data):
        ch = data.decode()
        if ch == '\n':
            try:
                debug.data(self.line_data + '\n')
                name = self._between_str(self.line_data, '<', '>')
                d = self._between_str(self.line_data, '[', ']')
                if name and d:
                    self.append(name, float(d))
                    self.data_cache.append("{} {} {}".format(name, d, self.cut_time_str()))
                self.line_data = ''
            except:
                debug.err('数据解析错误')
        else:
            self.line_data += ch

    def run(self):
        ''' 刷新显示的线程函数 '''
        while True:
            self.data_lock.lock()
            for curve in self.curves.values():
                curve.renew_diaplay()
            self.data_lock.unlock()
            QThread.msleep(20)
