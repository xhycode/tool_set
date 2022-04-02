# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread
from module.module_base import ModuleBase
from PyQt5.QtWidgets import QFileDialog
from ui import ui
import cfg
import debug
import time
import struct

PACK_SACP_VER = 1

PACK_TYPE_SM2 = 1
PACK_TYPE_A400 = 2
PACK_TYPE_J1 = 3
PACK_TYPE_SM2_MODULE = 4


# 创建升级包
def creat_update_packet(pack_type, index_range, version, flash_addr, app_path, out_path):
    '''
        pack_type: 包类型,见定义 eg. PACK_TYPE_SM2
        index_range: 元组类型 eg. (0, 100)
        version: 字符串类型 eg. 'V1.1.0'
        flash_addr: app在flash中的起始位置  eg. 0x8000000
        app_path:APP 文件的完整路径,包括app文件名 eg. './app.bin'
        out_path: 打包后的文件的输出路径 eg. './app_pack.bin'
    '''
    try:
        with open(app_path, 'rb') as app_file:
            app_bin = app_file.read()
        
        app_checknum = 0
        for c in app_bin:
            app_checknum = (app_checknum + c) & 0xFFFFFFF

        d = time.localtime()
        pack_time = "{}.{:02}.{:02}.{:02}.{:02}.{:02}\0".format(d.tm_year, d.tm_mon,d.tm_mday, d.tm_hour, d.tm_min, d.tm_sec).encode('UTF-8')
        print("pack time:", pack_time, " size:", len(pack_time))
        for i in range(33 - len(version)):
            version += '\0'
        with open(out_path, 'wb') as out_file:
            out_file.write("snapmaker update.bin\0".encode('UTF-8'))     # 21 B
            out_file.write(struct.pack('<B', PACK_SACP_VER))             # 1 B
            out_file.write(struct.pack('<H', pack_type))                 # 2 B
            out_file.write(struct.pack('<I', index_range[0]))            # 4 B
            out_file.write(struct.pack('<I', index_range[1]))            # 4 B
            out_file.write(version.encode('UTF-8'))                      # 32 B
            out_file.write(pack_time)                                    # 20 B
            out_file.write(struct.pack('<H', 0xFFFF))                    # 2 B
            out_file.write(struct.pack('<I', len(app_bin)))              # 4 B
            out_file.write(struct.pack('<I', app_checknum))              # 4 B
            out_file.write(struct.pack('<I', flash_addr))                # 4 B
            out_file.seek(512)
            out_file.write(app_bin)
        return True
    except Exception as e:
        print(e)
        return False

# SACP 协议
SACP_VERSION = 0x01
SACP_ID_PC          = 0
SACP_ID_CONTROLLER  = 1
SACP_ID_HMI         = 2

def sacp_check_data(data, length):
    checknum = 0
    if length > 0 :
      for i in range(0, (length - 1) , 2) :
        checknum += (((data[i]&0xff) << 8) | (data[i+1]&0xff))
      if length % 2 != 0:
        checknum += data[length - 1]
    while checknum > 0xffff:
      checknum = ((checknum >> 16) & 0xffff) + (checknum & 0xffff)
    checknum = ~checknum
    return checknum

def sacp_check_head(data, length):
    crc = 0
    poly = 0x07
    for i in range(length):
        for j in range(8):
            bit = ((data[i]&0xff) >> (7 - j) & 0x01) == 1
            c07 = ((crc)>> 7 & 0x01) == 1
            crc = crc << 1
            if (c07 ^ bit):
                crc ^= poly
    crc = crc & 0xff
    return crc

def sacp_pack(snd_id, rec_id, cmd_set, cmd_id, data, length, sequence, arrt):
    '''
        snd_id : 发送者ID
        rec_id : 接收者ID
        data : 要发送的数据
        lenght: 要发送数据长度
        sequence : 包的标号
        cmd_set : command_set
        cmd_id : command_id
        arrt : 0 - 请求, 1 - 应答
    '''
    sacp_head = struct.pack('<BBHBBBBBHBB', 
                            0xAA, 0x55, # 包头标识符
                            length + 6 + 2, # 包头从字节7到结尾有6个字节+数据末尾2个校验字节
                            SACP_VERSION, # 协议版本固定1
                            rec_id,
                            0,  # crc校验先写0占位
                            snd_id,
                            arrt,
                            sequence,
                            cmd_set,
                            cmd_id
                            )
    sacp_head = bytearray(sacp_head)
    sacp_head[6] = sacp_check_head(sacp_head, 6)
    pack_array = sacp_head + data
    checknum = sacp_check_data(pack_array[7:], length + 6)
    pack_array = pack_array + struct.pack("<H", checknum&0xFFFF)
    return pack_array

def sacp_unpack():
    pass


DATA_SORCE_SEND = 0
DATA_SORCE_RECV = 1

def _data_to_hex(data):
    temp = []
    for d in data:
        temp.append("{:0>2x}".format(d) + ' ')
        data = ''.join(temp)
    return data

def show_sacp_to_ui(source, sacp_data):
    '''
        source: DATA_SORCE_SEND / DATA_SORCE_RECV 发送的数据还是接收的数据
        sacp_data:原始数据
    '''
    out_info = "\n"
    if source == DATA_SORCE_SEND:
        out_info += "数据源:发送\n"
    elif source == DATA_SORCE_RECV:
        out_info += "数据源:接收\n"
    else:
        out_info += "数据源:未知\n"
    
    if sacp_data[0] != 0xAA and sacp_data[1] != 0x55:
        out_info += "数据类型不是SACP格式\n"
        out_info += "全部数据:"
        out_info += _data_to_hex(sacp_data)
    else:
        data_len = (sacp_data[2] | sacp_data[3] << 8) & 0xFFFF
        out_info += "数据长度:" + str(data_len)

        if data_len != len(sacp_data) - 7:  # 包头不算入长的数据有7个字节
            out_info += " (实际接收长度 {},有错误)\n".format(len(sacp_data) - 7)
        else:
            out_info += " (ok)\n"
        out_info += "协议版本:{}\n".format(sacp_data[4])
        out_info += "sender_id:{}  recever_id:{}\n".format(sacp_data[7], sacp_data[5])
        out_info += "crc 校验数:{:0>2x} ".format(sacp_data[6])
        crc = sacp_check_head(sacp_data, 6)
        if crc != sacp_data[6]:
            out_info += "(包头校验错误:0x{:0>2})\n".format(crc)
            out_info += "全部数据(hex): " + _data_to_hex(sacp_data) + "\n"
        else:
            out_info += "(ok)\n"

            out_info += "包类型:{:0>2x} ".format(sacp_data[8])
            if sacp_data[8] & 0x1:
                out_info += "(应答包)\n"
            else:
                out_info += "(请求包)\n"
            sequence = (sacp_data[9] | sacp_data[10] << 8) & 0xFFFF
            out_info += "sequence:{}\n".format(sequence)
            out_info += "cmd_set:0x{:0>2x}  cmd_id:0x{:0>2x}\n".format(sacp_data[11], sacp_data[12])

            recv_check = (sacp_data[-2] | sacp_data[-1] << 8) & 0xFFFF
            checknum = sacp_check_data(sacp_data[7:], data_len - 2) & 0xFFFF
            out_info += "数据校验码:0x{:0>4x}".format(recv_check)
            if recv_check != checknum:
                out_info += "(校验错误:0x{:0>4x})\n".format(checknum & 0xFFFF)
            else:
                out_info += "(ok)\n"
            out_info += "包头数据(hex): " + _data_to_hex(sacp_data[0: 13]) + "\n"
            out_info += "有效数据(hex): " + _data_to_hex(sacp_data[13: -2]) + "\n"
            out_info += "校验数(hex): " + _data_to_hex(sacp_data[-2:]) + "\n"
        out_info += "\n\n"
    ui.e_sacp_data_signal.emit(out_info)


def sacp_pack_from_ui(data):
    cmd_set = ui.sacp_debug_cmd_set.value() & 0xff
    cmd_id = ui.sacp_debug_cmd_id.value() & 0xff
    recv_id = ui.sacp_debug_recv_id.value() & 0xff
    send_id = ui.sacp_debug_send_id.value() & 0xff
    attr = ui.sacp_debug_attribute.value() & 0xffff
    sequence = ui.sacp_debug_sequence.value() & 0xffff
    pack = sacp_pack(send_id, recv_id, cmd_set, cmd_id, data, len(data), sequence, attr)
    show_sacp_to_ui(DATA_SORCE_SEND, pack)
    return pack

class SnapUpdateTool(QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        ModuleBase.__init__(self)
        self.update_tool_init()
        self.sacp_cache = []
        self.recv_status = 0

    def update_tool_init(self):
        ui.update_pack_app_file.clicked.connect(self.event_app_path)
        ui.update_pack_creat.clicked.connect(self.event_creat_update_pack)
        ui.sacp_debug_clean_data.clicked.connect(self.event_clean_debug_data)

    def event_app_path(self):
        path = "./app.bin"
        app_path = QFileDialog.getOpenFileName(ui, "Open upgrade file", path)[0]
        debug.info('path:' + app_path)
        ui.update_pack_app_path.setText(app_path)

    def event_creat_update_pack(self):
        out_file = QFileDialog.getSaveFileName(ui)[0]
        if out_file == '':
            debug.err("没有选择文件")
            return
        self.creat_update_packet(out_file)

    def event_clean_debug_data(self):
        ui.e_sacp_cache_data_signal.emit("")
        ui.e_sacp_data_signal.emit("")
        self.recv_status = 0
        self.sacp_cache = []

    def creat_update_packet(self, out_file):
        pack_type = ui.update_pack_type.value()
        debug.info('包类型：' + str(pack_type))
        index_range = (ui.update_pack_start_id.value(), ui.update_pack_start_id.value())
        debug.info('包ID范围:' + str(index_range))
        version = ui.update_pack_version.text()
        debug.info('包版本:' + version)
        flash_addr = ui.update_pack_flash_addr.value()
        debug.info('包flash地址:0x' + hex(flash_addr))
        app_path = ui.update_pack_app_path.text()
        debug.info('app路径:' + app_path)
        debug.info('输出路径:' + out_file)
        result = creat_update_packet(pack_type, index_range, version, flash_addr, app_path, out_file)
        if result != True:
            debug.err('packet failed')
        return result

    def sacp_event(self, sacp):
        pass


    def sacp_parse(self, b_data):
        status_flag = bytes.fromhex("aa 55")
        if self.recv_status == 0:
            # 还没有数据
            if b_data == status_flag[0]:
                self.sacp_cache.append(b_data)
                self.recv_status = 1
                ui.e_sacp_cache_data_signal.emit("{:0>2x} ".format(b_data))
        elif self.recv_status == 1:
            if b_data == status_flag[1]:
                self.sacp_cache.append(b_data)
                self.recv_status = 2
                ui.e_sacp_cache_data_signal.emit("{:0>2x} ".format(b_data))
            else:
                self.sacp_cache = []
                self.recv_status = 0
        elif self.recv_status == 2:
            self.sacp_cache.append(b_data)
            ui.e_sacp_cache_data_signal.emit("{:0>2x} ".format(b_data))
            if len(self.sacp_cache) >= 7:
                crc = sacp_check_head(self.sacp_cache, 6)
                if crc != self.sacp_cache[6]:
                    show_sacp_to_ui(self.sacp_cache)
                    self.sacp_cache = []
                    self.recv_status = 0
                else:
                    self.need_recv_len = (self.sacp_cache[2] | self.sacp_cache[3] << 8) & 0xFFFF
                    self.need_recv_len += 7
                    self.recv_status = 3
        elif self.recv_status == 3:
            self.sacp_cache.append(b_data)
            ui.e_sacp_cache_data_signal.emit("{:0>2x} ".format(b_data))
            if len(self.sacp_cache) == self.need_recv_len:
                show_sacp_to_ui(DATA_SORCE_RECV, self.sacp_cache)
                self.sacp_event(self.sacp_cache)
                self.sacp_cache = []
                self.recv_status = 0
                ui.e_sacp_cache_data_signal.emit("")

    # def run(self):
    #     while True:


if __name__ == '__main__':
    # creat_update_packet(PACK_TYPE_J1, (0, 100), "V1.1.0", 0x8000000, "d:/my_code/tool_set/module/sacp_update.py", "./app_pack.bin")
    data = bytes([1,2,3])
    head = sacp_pack(SACP_ID_HMI, SACP_ID_CONTROLLER, 1, 2, data, len(data), 1, 0)
    print(type(head))
    print("len:", len(head))
    print(head)