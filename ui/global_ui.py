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

TOOL_VERSIONS = 'V1.2.0'

class GloabalUI(QMainWindow, Ui_ToolSet):  # 继承类
    app = QApplication(sys.argv)

    '''外部在线程里边调用的小部件,需要提供一个自定义信号供外部使用，不然会出错'''
    # 调试信号窗口输出信号 str:要显示的字符串  bool:True-html数据;False-纯字符串
    e_debug_info_signal = QtCore.pyqtSignal(str, bool)

    # 数据显示窗口添加要显示的内容的信号 str:显示的内容
    e_recv_signal = QtCore.pyqtSignal(str)
    # 更新接收长度的信号  bool: True-数字累加  False-直接赋值
    set_lcd_recv_len_signal = QtCore.pyqtSignal(bool, int)

    # 刷新串口列表的信号  list串口列表; str:当前显示的串口
    serial_port_signal = QtCore.pyqtSignal(list, str)

    # 设置波形数据的信号 str:通道对应的名称 list:数据列表
    g_waveform_signal = QtCore.pyqtSignal(str, list)
    # 清空指定通道波形数据显示的信号 str:通道对应名称
    g_waveform_clear_signal = QtCore.pyqtSignal(str)
   

    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 执行类中的setupUi函数
        self.setWindowTitle("调试工具箱 " + TOOL_VERSIONS)
        self.setWindowOpacity(0.96)
        # self.setStyleSheet('background-color:#050505')
        # self.setStyleSheet('foreground-color:#000000')
        self.icon_init()
        self.init_waveform_ui()
        self.signal_init()
    
    def icon_init(self):
        '''界面坐上角显示的图标'''
        self.setWindowIcon(QIcon('./ui/mao.png'))

    def signal_init(self):
        '''将开头定义的信号量绑定处理函数'''
        self.e_recv_signal.connect(self.renew_recv_dispay)
        self.set_lcd_recv_len_signal.connect(self.set_lcd_recv_len)
        self.e_debug_info_signal.connect(self.debug_dispay)
        self.serial_port_signal.connect(self.renew_serial_port)
        self.g_waveform_clear_signal.connect(self.clear_curves)
        self.g_waveform_signal.connect(self.set_waveform_data)

    def renew_recv_dispay(self, data):
        ''' 数据界面添加内容，数据会追加到最后边显示
            data: 要显示的数据，str类型
        '''
        self.e_recv.moveCursor(QTextCursor.End)
        self.e_recv.insertPlainText(data)
        self.e_recv.moveCursor(QTextCursor.End)
    
    def set_lcd_recv_len(self, is_add, num):
        ''' 设置接收数据长度的显示
        is_add: True-数字累加 类型: bool
        num: 更新的数字  类型:int
        '''
        if is_add:
            self.e_recv_len.setText(str(int(self.e_recv_len.displayText()) + num))
        else:
            self.e_recv_len.setText(str(num))

    def text_all_black(self, text_edit):
        ''' 将所有的字体都变成黑色
            text_edit: 要做修改的部件 类型: QTextEdit
        '''
        col = QColor('black')
        fmt = QTextCharFormat()
        fmt.setForeground(col)
        text_edit.selectAll()
        text_edit.setCurrentCharFormat(fmt)

    def _highlight_selection(self, text_edit, format):
        ''' 高亮选中的符串
            text_edit: 要做修改的部件 类型: QTextEdit
            format : 指定的字符串格式 类型: QTextCharFormat
        '''
        cursor = text_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(format)
        text_edit.mergeCurrentCharFormat(format)
    
    def highlight_text(self, text_edit, text, color):
        ''' QTextEdit 中的部分字体高亮
            text_edit: 待操作的小部件 
            text: 要高亮的字符串
            color：字符串颜色
        '''
        self.text_all_black(text_edit)
        col = QColor(color)
        fmt = QTextCharFormat()
        fmt.setForeground(col)
        if not text:
            return
        if not col.isValid():
            return
        # 先把光标移动到开头, 然后全文查找
        text_edit.moveCursor(QTextCursor.Start)
        while text_edit.find(text):  # 查找所有文字
            self._highlight_selection(text_edit, fmt)

    def renew_serial_port(self, port_list, cur):
        ''' 刷新串口列表
            port_list: 串口列表  类型: list
            cur : 当前要显示的端口 类型:str
            如果列表中没有 cur 端口则显示列表第一个
        '''
        self.serial_port.clear()
        self.serial_port.addItems(port_list)
        print(port_list)
        if cur in port_list:
            self.serial_port.setCurrentText(cur)
        elif len(port_list) > 0:
            self.serial_port.setCurrentText(port_list[0])

    def debug_dispay(self, data, is_html):
        ''' 调试窗口输出信息
            data: 要显示的信息 类型: str
            is_html: True-按照html显示  False-纯字符显示  类型: bool
            由于没有清空的操作，所以会限制显示的量
        '''
        text = self.e_debug_info.toPlainText()
        if len(text) > 4096:  # 大小现在在4k，超过就砍半
            self.e_debug_info.clear()
            self.e_debug_info.insertPlainText(text[2048:])
        self.e_debug_info.moveCursor(QTextCursor.End)
        if is_html:
            self.e_debug_info.insertHtml(data)
        else:
            self.e_debug_info.insertPlainText(data)

    # ############ 波形界面相关方法 ##################

    def init_waveform_ui(self):
        ''' 波形显示界面初始化
        '''
        self.g_waveform.setBackground('w')
        self.g_waveform.addLegend()
        self.g_waveform.showGrid(x=True, y=True, alpha=0.5)
        self.g_waveform.setLabels(left='y', bottom='x',title='y/x')
        self.curves = {}  # 存放 通道名:曲线 组成的字典

    def set_waveform_data(self, name, data):
        ''' 将数据设置到指定的通道显示
            name: 通道名称 类型: str
            data: 要显示的数据 类型: list
        '''
        if self.curves.get(name, None):
            self.curves[name].setData(data)

    def get_curves(self, name):
        ''' 获取指定通道的曲线
            name: 通道名字 类型: str
            返回: 曲线类 找不到返回 None
        '''
        return self.curves.get(name, None)

    def add_curves(self, name):
        ''' 添加一个曲线显示通道
            name:通道名 类型: str
        '''
        COLOR = ['b', 'g', 'r', 'c', 'm', 'y', 'w', 'k']
        color = COLOR[len(self.curves) % len(COLOR)]
        self.curves[name] = self.g_waveform.plot(pen=color, name=name)

    def clear_curves(self, name):
        ''' 清除一个通道的显示
            name:通道的名字 类型:str
        '''
        if self.curves.get(name, None):
            self.curves[name].clear()
