# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtWidgets, QtGui
from ui.main_window import Ui_ToolSet
import pyqtgraph
import sys

TOOL_VERSIONS = 'V1.0.0'

class GloabalUI(QtWidgets.QMainWindow, Ui_ToolSet):  # 继承类
    app = QApplication(sys.argv)
    '''外部在线程里边调用的小部件,需要提供一个自定义信号供外部使用，不然会出错'''
    e_recv_signal = QtCore.pyqtSignal(str)
    e_debug_info_signal = QtCore.pyqtSignal(str)
    serial_port_signal = QtCore.pyqtSignal(list, str)
    g_waveform_signal = QtCore.pyqtSignal(str, list)
    g_waveform_clear_signal = QtCore.pyqtSignal(str)
    set_lcd_recv_len_signal = QtCore.pyqtSignal(bool, int)

    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 执行类中的setupUi函数
        self.setWindowTitle("调试工具箱 " + TOOL_VERSIONS)
        self.init_waveform_ui()
        self.e_recv_signal.connect(self.renew_recv_dispay)
        self.e_debug_info_signal.connect(self.debug_dispay)
        self.serial_port_signal.connect(self.renew_serial_port)
        self.g_waveform_clear_signal.connect(self.clear_curves)
        self.g_waveform_signal.connect(self.set_waveform_data)
        self.set_lcd_recv_len_signal.connect(self.set_lcd_recv_len)

    def renew_recv_dispay(self, data):
        self.e_recv.moveCursor(QtGui.QTextCursor.End)
        self.e_recv.insertPlainText(data)

    def renew_serial_port(self, port_list, cur):
        self.serial_port.clear()
        self.serial_port.addItems(port_list)
        print(port_list)
        if cur in port_list:
            self.serial_port.setCurrentText(cur)
        elif len(port_list) > 0:
            self.serial_port.setCurrentText(port_list[0])

    def debug_dispay(self, data):
        self.e_debug_info.moveCursor(QtGui.QTextCursor.End)
        self.e_debug_info.insertPlainText(data)

    def set_lcd_recv_len(self, flag, num):
        if flag:
            self.lcd_recv_len.display(self.lcd_recv_len.value() + num)
        else:
            self.lcd_recv_len.display(num)

    # ############ 波形界面相关方法 ##################

    def init_waveform_ui(self):
        self.g_waveform.setBackground('w')
        self.g_waveform.addLegend()
        self.g_waveform.showGrid(x=True, y=True, alpha=0.5)
        self.g_waveform.setLabels(left='y', bottom='x',title='y/x')
        self.curves = {}

    def set_waveform_data(self, name, data):
        if self.curves.get(name, None):
            self.curves[name].setData(data)

    def get_curves(self, name):
        return self.curves.get(name, None)

    def add_curves(self, name):
        COLOR = ['b', 'g', 'r', 'c', 'm', 'y', 'w', 'k']
        color = COLOR[len(self.curves) % len(COLOR)]
        self.curves[name] = self.g_waveform.plot(pen=color, name=name)

    def clear_curves(self, name):
        if self.curves.get(name, None):
            self.curves[name].clear()
