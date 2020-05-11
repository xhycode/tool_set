from configobj import ConfigObj

CFG_FILE = "cfg.ini"
SERIAL_PORT = 'serial_port'
SERIAL_BAUDRATE = 'serial_baudrate'
DATA_FONT_SIZE = 'data_font_size'
WAVEFORM_CACHE = 'waveform_cache_size'
LAST_MODULE_INDEX = 'module_index'
EXTEND_ENTER_STATE = 'extend_enter_state'
EXTEND_CYCLIC = 'extend_cyclic'
HEX_SEND_STATE = 'hex_send'
AUTO_SELD_TIME = 'auto_send_time'
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
