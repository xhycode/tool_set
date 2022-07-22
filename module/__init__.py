# -*- coding: utf-8 -*-

from module import module_base
from module import waveform
from module import data_display
from module import snap_ctrl
from ui import ui
import cfg


MODULE_TYPE_DISPLAY = 0
MODULE_TYPE_WAVEFORM = 1
MODULE_TYPE_SNAP_CTRL = 2
class ModuleManage(module_base.ModuleBase):
    def __init__(self):
        pass
        self._mode_win = ui.mode_manage
        self._mode_win.currentChanged.connect(self._event_chenge)
        self._module_table = {MODULE_TYPE_DISPLAY: data_display.DataDisplay(),
                             MODULE_TYPE_WAVEFORM: waveform.Waveform(),
                             MODULE_TYPE_SNAP_CTRL: snap_ctrl.SnapControl()}
        self._set_cur_module()

    def _set_cur_module(self):
        last_index = int(cfg.get(cfg.LAST_MODULE_INDEX, '0'))
        self._mode_win.setCurrentIndex(last_index)
        self._cur_module = self._module_table[last_index]
        self.cur_module_index = last_index

    def _event_chenge(self):
        self.cur_module_index = self._mode_win.currentIndex()
        self._cur_module = self._module_table[self.cur_module_index]
        cfg.set(cfg.LAST_MODULE_INDEX, str(self.cur_module_index))

    def parse(self, data):
        if self.cur_module_index != MODULE_TYPE_DISPLAY and not self._module_table[MODULE_TYPE_SNAP_CTRL].is_print_work():
            self._module_table[MODULE_TYPE_DISPLAY].parse(data)
        if self.cur_module_index != MODULE_TYPE_SNAP_CTRL and self._module_table[MODULE_TYPE_SNAP_CTRL].is_print_work():
            self._module_table[MODULE_TYPE_SNAP_CTRL].parse(data)
        else:
            self._cur_module.parse(data)

    def send_pop(self):
        if self.cur_module_index != MODULE_TYPE_SNAP_CTRL and self._module_table[MODULE_TYPE_SNAP_CTRL].is_print_work():
            return self._module_table[MODULE_TYPE_SNAP_CTRL].send_pop()
        return self._cur_module.send_pop()

