# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtWidgets, QtGui
from ui.main_window import Ui_ToolSet
import sys

TOOL_VERSIONS = 'V1.0.0'

class GloabalUI(QtWidgets.QMainWindow, Ui_ToolSet):  # 继承类
    app = QApplication(sys.argv)
    '''外部在线程里边调用的小部件,需要提供一个自定义信号供外部使用，不然会出错'''
    e_recv_signal = QtCore.pyqtSignal(str)
    e_debug_info_signal = QtCore.pyqtSignal(str)
    serial_port_signal = QtCore.pyqtSignal(list, int)
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 执行类中的setupUi函数
        self.setWindowTitle("调试工具箱 " + TOOL_VERSIONS)
        self.e_recv_signal.connect(self.renew_recv_dispay)
        self.e_debug_info_signal.connect(self.debug_dispay)
        self.serial_port_signal.connect(self.renew_serial_port)

    def renew_recv_dispay(self, data):
        self.e_recv.moveCursor(QtGui.QTextCursor.End)
        self.e_recv.insertPlainText(data);
    
    def renew_serial_port(self, port_list, cur):
        self.serial_port.clear()
        self.serial_port.addItems(port_list)
        print(port_list)

        if cur in port_list:
            self.serial_port.setCurrentText(port_list.index(cur))
        else:
            self.serial_port.setCurrentText('')

    def debug_dispay(self, data):
        self.e_debug_info.moveCursor(QtGui.QTextCursor.End)
        self.e_debug_info.insertPlainText(data);

