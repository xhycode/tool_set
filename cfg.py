from configobj import ConfigObj

CFG_FILE = "cfg.ini"
SERIAL_PORT = 'serial_port'
SERIAL_BAUDRATE = 'serial_baudrate'
DATA_FONT_SIZE = 'data_font_size'

config = ConfigObj(CFG_FILE, encoding='UTF8')
if len(config) == 0:
    config[SERIAL_PORT] = 'COM3'
    config[SERIAL_BAUDRATE] = '115200'
    config[DATA_FONT_SIZE] = '9'
    config.write()

config = ConfigObj(CFG_FILE, encoding='UTF8')

def get(name):
    return config[name]

def set(name, var):
    config[name] = var
    config.write()
