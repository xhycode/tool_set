from ui import ui


def data(info):
    print(info)
    ui.e_debug_info_signal.emit(info, False)


def info(info):
    print(info)
    i = '<body><p style="color:green;">{}</p><br></body>'.format(info)
    '''将要显示的字符串信息输出到调试窗口'''
    ui.e_debug_info_signal.emit(i, True)


def err(info):
    print(info)
    i = '<body><p style="color:red;">{}</p><br></body>'.format(info)
    '''将要显示的字符串信息输出到调试窗口'''
    ui.e_debug_info_signal.emit(i, True)