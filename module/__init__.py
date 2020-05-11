# -*- coding: utf-8 -*-

from module import module_base
from module import waveform
from module import data_display
from ui import ui

class ModuleManage(module_base.ModuleBase):
    def __init__(self):
        pass
        self._mode_win = ui.mode_manage
        self._mode_win.currentChanged.connect(self._event_chenge)
        self._module_table = {0: data_display.DataDisplay(),
                             1: waveform.Waveform()}
        self._set_cur_module()

    def _set_cur_module(self):
        self._cur_module = self._module_table[self._mode_win.currentIndex()]

    def _event_chenge(self):
        print(self._mode_win.currentIndex())
        self._set_cur_module()

    def parse(self, data):
        self._cur_module.parse(data)


