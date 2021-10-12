from configobj import ConfigObj


CFG_FILE = "cfg.ini"
SERIAL_PORT = 'serial_port'
SERIAL_BAUDRATE = 'serial_baudrate'
DATA_FONT_SIZE = 'data_font_size'
WAVEFORM_CACHE = 'waveform_cache_size'
LAST_MODULE_INDEX = 'module_index'
EXTEND_ENTER_STATE = 'extend_enter_state'
SEND_ENTER_STATE = 'send_enter_state'
EXTEND_CYCLIC = 'extend_cyclic'
HEX_SEND_STATE = 'hex_send'
AUTO_SEND_TIME = 'auto_send_time'
MSG_CONNRET_MODE = 'connect_mode'
TCP_CLIENT_IP = 'tcp_client_ip'
TCP_CLIENT_PORT = 'tcp_client_port'
SEND_ENCODE = 'send_encode'
DISPLAY_ENCODE = 'display_encode'
SERVER_PORT = 'server_port'
config = ConfigObj(CFG_FILE, encoding='UTF8')


def get(name, default=''):
    if config.get(name):
        return config[name]
    else:
        config[name] = default
        config.write()
        return default


def set(name, var):
    config[name] = var
    config.write()
