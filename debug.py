from ui import ui


def info(info):
    print(info)
    '''将要显示的字符串信息输出到调试窗口'''
    ui.e_debug_info_signal.emit(info)


def info_ln(info):
    print(info+'\n')
    '''将要显示的字符串信息输出到调试窗口'''
    ui.e_debug_info_signal.emit(info+'\n')