# -*- coding: utf-8 -*-

from module import module_base
from module import waveform
from module import data_display
from ui import ui
import cfg

class ModuleManage(module_base.ModuleBase):
    def __init__(self):
        pass
        self._mode_win = ui.mode_manage
        self._mode_win.currentChanged.connect(self._event_chenge)
        self._module_table = {0: data_display.DataDisplay(),
                             1: waveform.Waveform()}
        self._set_cur_module()

    def _set_cur_module(self):
        last_index = int(cfg.get(cfg.LAST_MODULE_INDEX, '0'))
        self._mode_win.setCurrentIndex(last_index)
        self._cur_module = self._module_table[last_index]

    def _event_chenge(self):
        cur_index = self._mode_win.currentIndex()
        self._cur_module = self._module_table[cur_index]
        cfg.set(cfg.LAST_MODULE_INDEX, str(cur_index))

    def parse(self, data):
        self._cur_module.parse(data)


