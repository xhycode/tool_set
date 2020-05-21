# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QTextCharFormat
from PyQt5.QtGui import QTextDocument
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QIcon
from ui.main_window import Ui_ToolSet
import sys

TOOL_VERSIONS = 'V1.1.0'

class GloabalUI(QMainWindow, Ui_ToolSet):  # 继承类
    app = QApplication(sys.argv)
    '''外部在线程里边调用的小部件,需要提供一个自定义信号供外部使用，不然会出错'''
    e_recv_signal = QtCore.pyqtSignal(str)
    e_debug_info_signal = QtCore.pyqtSignal(str, bool)
    serial_port_signal = QtCore.pyqtSignal(list, str)
    g_waveform_signal = QtCore.pyqtSignal(str, list)
    g_waveform_clear_signal = QtCore.pyqtSignal(str)
    set_lcd_recv_len_signal = QtCore.pyqtSignal(bool, int)

    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 执行类中的setupUi函数
        self.setWindowTitle("调试工具箱 " + TOOL_VERSIONS)
        self.icon_init()
        self.init_waveform_ui()
        self.e_recv_signal.connect(self.renew_recv_dispay)
        self.e_debug_info_signal.connect(self.debug_dispay)
        self.serial_port_signal.connect(self.renew_serial_port)
        self.g_waveform_clear_signal.connect(self.clear_curves)
        self.g_waveform_signal.connect(self.set_waveform_data)
        self.set_lcd_recv_len_signal.connect(self.set_lcd_recv_len)
    
    def icon_init(self):
        self.setWindowIcon(QIcon('./ui/mao.png'))

    def renew_recv_dispay(self, data):
        self.e_recv.moveCursor(QTextCursor.End)
        self.e_recv.insertPlainText(data)

    def highlight_selection(self, text_edit, format):
        cursor = text_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(format)
        text_edit.mergeCurrentCharFormat(format)
    
    def text_all_black(self, text_edit):
        col = QColor('black')
        fmt = QTextCharFormat()
        fmt.setForeground(col)
        text_edit.selectAll()
        text_edit.setCurrentCharFormat(fmt)

    def highlight_text(self, text_edit, text, color):
        self.text_all_black(text_edit)
        col = QColor(color)
        fmt = QTextCharFormat()
        fmt.setForeground(col)
        if not text:
            return
        if not col.isValid():
            return
        # 先把光标移动到开头
        text_edit.moveCursor(QTextCursor.Start)
        while text_edit.find(text):  # 查找所有文字
            self.highlight_selection(text_edit, fmt)

    def renew_serial_port(self, port_list, cur):
        self.serial_port.clear()
        self.serial_port.addItems(port_list)
        print(port_list)
        if cur in port_list:
            self.serial_port.setCurrentText(cur)
        elif len(port_list) > 0:
            self.serial_port.setCurrentText(port_list[0])

    def debug_dispay(self, data, is_html):
        text = self.e_debug_info.toPlainText()
        if len(text) > 4096:  # 大小现在在4k，超过就砍半
            self.e_debug_info.clear()
            self.e_debug_info.insertPlainText(text[2048:])
        self.e_debug_info.moveCursor(QTextCursor.End)
        if is_html:
            self.e_debug_info.insertHtml(data)
        else:
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
