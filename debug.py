from ui import ui


def info(info):
    '''将要显示的字符串信息输出到调试窗口'''
    ui.e_debug_info_signal.emit(info)


def info_ln(info):
    '''将要显示的字符串信息输出到调试窗口'''
    ui.e_debug_info_signal.emit(info+'\n')