from ui import ui


def data(info):
    print(info)
    ui.e_debug_info_signal.emit(info, False)


def info(info):
    print(info)
    i = '<body><p style="color:green;">{}</p><br></body>'.format(info)
    ui.e_debug_info_signal.emit(i, True)


def err(info):
    print(info)
    i = '<body><p style="color:red;">{}</p><br></body>'.format(info)
    ui.e_debug_info_signal.emit(i, True)