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
UPDATE_PACK_HEAD_SIZE = 256

PACK_HEAD_FLAG_STR = 'snapmaker update.bin\0'
TEMP_PACKET_PATH = "temp_packet.bin"

# SACP 协议
SACP_VERSION = 0x01
SACP_ID_PC          = 0
SACP_ID_CONTROLLER  = 1
SACP_ID_HMI         = 2
SACP_ATTR_REQ = 0
SACP_ATTR_ACK = 1

DATA_SORCE_SEND = 0
DATA_SORCE_RECV = 1
DATA_SORCE_UNKNOW = 3


COMMAND_SET_UPDATE        = 0xAD
UPDATE_ID_REQ_UPDATE      = 0x01
UPDATE_ID_REQ_UPDATE_PACK = 0x02
UPDATE_ID_REPORT_STATUS   = 0x03

def sacp_check_data(data, length):
    checknum = 0
    if length > 0 :
      for i in range(0, (length - 1) , 2) :
        checknum += (((data[i]&0xff) << 8) | (data[i+1]&0xff))
        checknum &= 0xffffffff
      if length % 2 != 0:
        checknum += data[length - 1]
    while checknum > 0xffff:
      checknum = ((checknum >> 16) & 0xffff) + (checknum & 0xffff)
    checknum = ~checknum
    return checknum & 0xffffffff


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

        d = time.localtime()
        pack_time = "{}.{:02}.{:02}.{:02}.{:02}.{:02}\0".format(d.tm_year, d.tm_mon,d.tm_mday, d.tm_hour, d.tm_min, d.tm_sec).encode('UTF-8')
        print("pack time:", pack_time, " size:", len(pack_time))
        for i in range(32 - len(version)):
            version += '\0'

        pack_head = PACK_HEAD_FLAG_STR.encode('UTF-8')            # 21 B
        pack_head += struct.pack('<B', PACK_SACP_VER)             # 1 B
        pack_head += struct.pack('<H', pack_type)                 # 2 B
        pack_head += struct.pack('<H', index_range[0])            # 4 B
        pack_head += struct.pack('<H', index_range[1])            # 4 B
        pack_head += version.encode('UTF-8')                      # 32 B
        pack_head += pack_time                                    # 20 B
        pack_head += struct.pack('<H', 0xAA01)                    # 2 B
        pack_head += struct.pack('<I', len(app_bin))              # 4 B
        app_checknum = sacp_check_data(app_bin, len(app_bin))
        pack_head += struct.pack('<I', app_checknum)              # 4 B
        pack_head += struct.pack('<I', flash_addr)                # 4 B

        pack_checknum = sacp_check_data(pack_head, len(pack_head))
        pack_head += struct.pack('<I', pack_checknum)                # 4 B

        with open(out_path, 'wb') as out_file:
            out_file.write(pack_head)
            out_file.seek(UPDATE_PACK_HEAD_SIZE)
            out_file.write(app_bin)
            out_file.close()
        return True
    except Exception as e:
        debug.err(e)
        return False


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


def sacp_pack_from_ui(data):
    '''
        给界面串口发送区提供的接口
    '''
    cmd_set = ui.sacp_debug_cmd_set.value() & 0xff
    cmd_id = ui.sacp_debug_cmd_id.value() & 0xff
    recv_id = ui.sacp_debug_recv_id.value() & 0xff
    send_id = ui.sacp_debug_send_id.value() & 0xff
    attr = ui.sacp_debug_attribute.value() & 0xffff
    sequence = ui.sacp_debug_sequence.value() & 0xffff
    pack = sacp_pack(send_id, recv_id, cmd_set, cmd_id, data, len(data), sequence, attr)
    SacpStruct(pack).show_to_ui(DATA_SORCE_SEND)
    return pack


class SacpStruct:
    def __init__(self, sacp_data=None):
        if sacp_data == None:
            self.is_sacp_data = False
        else:
            self.parse_data(sacp_data)

    def parse_data(self, sacp_data):
        self.all_data = sacp_data[:]
        if (sacp_data[0] != 0xAA and sacp_data[1] != 0x55) or len(sacp_data) < 13:
            self.is_sacp_data = False
        else:
            self.is_sacp_data = True
            self.data_len = (sacp_data[2] | sacp_data[3] << 8) & 0xFFFF
            if self.data_len != len(sacp_data) - 7:  # 包头不算入长的数据有7个字节
                self.is_len_ok = False
            else:
                self.is_len_ok = True
            self.sacp_ver = sacp_data[4]
            self.sender_id = sacp_data[7]
            self.recever_id = sacp_data[5]
            self.recv_crc = sacp_data[6]
            self.calc_crc = sacp_check_head(sacp_data, 6)
            if self.recv_crc != self.calc_crc:
                self.is_crc_ok = False
            else:
                self.is_crc_ok = True
                self.arrt = sacp_data[8]
                self.sequence = (sacp_data[9] | sacp_data[10] << 8) & 0xFFFF
                self.cmd_set = sacp_data[11]
                self.cmd_id = sacp_data[12]
                self.recv_checknum = (sacp_data[-2] | sacp_data[-1] << 8) & 0xFFFF
                self.calc_checknum = sacp_check_data(sacp_data[7:], self.data_len - 2) & 0xFFFF
                if self.recv_checknum != self.calc_checknum:
                    self.is_checknum_ok = False
                else:
                    self.is_checknum_ok = True
                self.head_data = sacp_data[0: 13]
                self.valid_data = sacp_data[13: -2]

    def _data_to_hex(self, data):
        if len(data) == 0:
            return ''
        temp = []
        for d in data:
            temp.append("{:0>2x}".format(d) + ' ')
            data = ''.join(temp)
        return data

    def show_to_ui(self, source=DATA_SORCE_UNKNOW):
        '''
            source: DATA_SORCE_SEND / DATA_SORCE_RECV 发送的数据还是接收的数据
        '''
        out_info = "\n"
        if source == DATA_SORCE_SEND:
            out_info += "数据源:发送\n"
        elif source == DATA_SORCE_RECV:
            out_info += "数据源:接收\n"
        else:
            out_info += "数据源:未知\n"
        
        if not self.is_sacp_data:
            out_info += "数据类型不是SACP格式\n"
            out_info += "全部数据:"
            out_info += self._data_to_hex(self.all_data)
        else:
            out_info += "数据长度:" + str(self.data_len)

            if not self.is_crc_ok:
                out_info += " (实际接收长度 {},有错误)\n".format(len(self.all_data) - 7)
                out_info += "全部数据(hex): " + self._data_to_hex(self.all_data) + "\n"
            else:
                out_info += " (ok)\n"
                out_info += "有效数据长度:" + str(self.data_len - 8) + '\n'
                out_info += "协议版本:{}\n".format(self.sacp_ver)
                out_info += "sender_id:{}  recever_id:{}\n".format(self.sender_id, self.recever_id)
                out_info += "crc 校验数:{:0>2x} ".format(self.recv_crc)
                if not self.is_crc_ok:
                    out_info += "(包头校验错误:0x{:0>2})\n".format(self.calc_crc)
                    out_info += "全部数据(hex): " + self._data_to_hex(self.all_data) + "\n"
                else:
                    out_info += "(ok)\n"
                    out_info += "包类型:{:0>2x} ".format(self.arrt)
                    if self.arrt & 0x1:
                        out_info += "(应答包)\n"
                    else:
                        out_info += "(请求包)\n"
                    out_info += "sequence:{}\n".format(self.sequence)
                    out_info += "cmd_set:0x{:0>2x}  cmd_id:0x{:0>2x}\n".format(self.cmd_set, self.cmd_id)
                    out_info += "数据校验码:0x{:0>4x}".format(self.recv_checknum)
                    if not self.is_checknum_ok:
                        out_info += "(校验错误:0x{:0>4x})\n".format(self.calc_checknum & 0xFFFF)
                        out_info += "全部数据(hex): " + self._data_to_hex(self.all_data) + "\n"
                    else:
                        out_info += "(ok)\n"
                        out_info += "包头数据(hex): " + self._data_to_hex(self.head_data) + "\n"
                        out_info += "有效数据(hex): " + self._data_to_hex(self.valid_data) + "\n"
            out_info += "\n\n"
        ui.e_sacp_data_signal.emit(out_info)

    def is_have_data(self):
        if not self.is_sacp_data:
            return False
        if not self.is_crc_ok:
            return False
        if not self.is_checknum_ok:
            return False
        return True

    def get_cmd_set(self):
        return self.cmd_set

    def get_cmd_id(self):
        return self.cmd_id

    def get_sequence(self):
        return self.sequence

    def get_valid_data(self):
        return self.valid_data, self.data_len

class SnapUpdateTool(QThread):
    def __init__(self, send_bytes):
        super().__init__()
        self.send_bytes = send_bytes
        self.update_tool_init()
        self.sacp_cmd = SacpStruct()
        self.sacp_cache = []
        self.recv_status = 0
        self.update_file = None
        self.sequence = 0

    def update_tool_init(self):
        ui.update_pack_app_file.clicked.connect(self.event_app_path)
        ui.update_pack_creat.clicked.connect(self.event_creat_update_pack)
        ui.sacp_debug_clean_data.clicked.connect(self.event_clean_debug_data)
        ui.update_start_button.clicked.connect(self.event_update_app)
        ui.sacp_debug_parse_cache.clicked.connect(self.event_parse_cache_date)

    def send_sacp(self, data):
        SacpStruct(data).show_to_ui(DATA_SORCE_SEND)
        self.send_bytes(data)

    def get_sequence(self):
        self.sequence += 1
        return self.sequence & 0xffff

    def event_parse_cache_date(self):
        try:
            data = ui.sacp_debug_cache_data.toPlainText()
            sacp_data = bytes.fromhex(data)
            print(sacp_data)
            SacpStruct(sacp_data).show_to_ui(DATA_SORCE_SEND)
        except:
            debug.err("格式错误.举例“01 02”")

    def event_app_path(self):
        path = ui.update_pack_app_path.text()
        app_path = QFileDialog.getOpenFileName(ui, "Open upgrade file", path)[0]
        debug.info('path:' + app_path)
        ui.update_pack_app_path.setText(app_path)

    def event_creat_update_pack(self):
        out_file = QFileDialog.getSaveFileName(ui)[0]
        if out_file == '':
            debug.err("没有选择文件")
            return
        app_path = ui.update_pack_app_path.text()
        self.creat_update_packet(app_path, out_file)

    def event_clean_debug_data(self):
        ui.e_sacp_cache_data_signal.emit("")
        ui.e_sacp_data_signal.emit("")
        self.recv_status = 0
        self.sacp_cache = []

    def event_update_app(self):
        path = ui.last_update_file_path.text()
        app_path = QFileDialog.getOpenFileName(ui, "Open upgrade file", path)[0]
        debug.info('path:' + app_path)
        if app_path == '':
            debug.err('没有选择升级文件')
            return
        ui.e_set_update_progress_signal.emit(0)
        ui.last_update_file_path.setText(app_path)
        with open(app_path, 'rb') as f:
            self.update_file = f.read()
            f.close()
        need_pack = False
        try:
            file_type = self.update_file[:21].decode('utf-8')
            if PACK_HEAD_FLAG_STR not in file_type:
                need_pack = True
        except:
            need_pack = True
        if need_pack:
            debug.info('非打包文件,工具根据左边参数打包')
            self.creat_update_packet(app_path, TEMP_PACKET_PATH)
            with open(TEMP_PACKET_PATH, 'rb') as f:
                self.update_file = f.read()
                f.close()
        else:
            debug.info('正常升级包')
        update_head = sacp_pack(SACP_ID_HMI, SACP_ID_CONTROLLER, COMMAND_SET_UPDATE, UPDATE_ID_REQ_UPDATE,
                self.update_file[ : UPDATE_PACK_HEAD_SIZE], UPDATE_PACK_HEAD_SIZE, self.get_sequence(), SACP_ATTR_REQ)
        self.send_sacp(update_head)
        self.send_data_bak = bytes()


    def creat_update_packet(self, app_path, out_file):
        pack_type = ui.update_pack_type.value()
        debug.info('包类型：' + str(pack_type))
        index_range = (ui.update_pack_start_id.value(), ui.update_pack_end_id.value())
        debug.info('包ID范围:' + str(index_range))
        version = ui.update_pack_version.text()
        debug.info('包版本:' + version)
        flash_addr = ui.update_pack_flash_addr.value()
        debug.info('包flash地址:0x' + hex(flash_addr))
        debug.info('app路径:' + app_path)
        debug.info('输出路径:' + out_file)
        result = creat_update_packet(pack_type, index_range, version, flash_addr, app_path, out_file)
        if result != True:
            debug.err('packet failed')
        return result

    def send_update_pack(self):
        recv_data, recv_len = self.sacp_cmd.get_valid_data()
        start_addr = recv_data[0] | recv_data[1] << 8 | recv_data[2] << 16 | recv_data[3] << 24
        max_size = recv_data[4] | recv_data[5] << 8
        if self.update_file == None:
            debug.err("没有升级文件")
            return
        file_len = len(self.update_file)
        file_addr = UPDATE_PACK_HEAD_SIZE + start_addr
        if file_addr + 1 > file_len:
            debug.err("请求的地址超出文件")
            data = bytes()
            result = 1
        elif file_addr + max_size < file_len:
            data = self.update_file[file_addr: file_addr + max_size]
            result = 0
        else:
            data = self.update_file[file_addr:]
            result = 0
        end_addr = start_addr
        if len(data) > 1:
            end_addr = start_addr + len(data) - 1
        pack_info = struct.pack("<BII", result, start_addr, end_addr) + data
        update_pack = sacp_pack(SACP_ID_HMI, SACP_ID_CONTROLLER, COMMAND_SET_UPDATE, UPDATE_ID_REQ_UPDATE_PACK,
                pack_info, len(pack_info), self.sacp_cmd.get_sequence(), SACP_ATTR_ACK)
        self.send_sacp(update_pack)
        ui.e_set_update_progress_signal.emit(end_addr / (file_len - UPDATE_PACK_HEAD_SIZE) * 100)
        self.send_data_bak += data

    def update_status_deal(self):
        result = self.sacp_cmd.get_valid_data()[0]
        ui.e_set_update_progress_signal.emit(100)
        check = sacp_check_data(self.send_data_bak, len(self.send_data_bak))
        debug.info("发送校验:{:0>4x}".format(check))

        if result[0] != 0:
            debug.err("升级失败:{}".format(result))
        else:
            debug.info('升级成功')

    def sacp_event(self):
        cmd_set = self.sacp_cmd.get_cmd_set()
        cmd_id = self.sacp_cmd.get_cmd_id()
        if cmd_set == COMMAND_SET_UPDATE:
            if cmd_id == UPDATE_ID_REQ_UPDATE_PACK:
                self.send_update_pack()
            elif cmd_id == UPDATE_ID_REPORT_STATUS:
                self.update_status_deal()

    def sacp_recv_end(self):
        self.sacp_cmd.parse_data(self.sacp_cache)
        self.sacp_cmd.show_to_ui(DATA_SORCE_RECV)
        self.sacp_cache = []
        self.recv_status = 0
        ui.e_sacp_cache_data_signal.emit("")
        if self.sacp_cmd.is_have_data():
            self.sacp_event()


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
                    self.sacp_recv_end()
                else:
                    self.need_recv_len = (self.sacp_cache[2] | self.sacp_cache[3] << 8) & 0xFFFF
                    self.need_recv_len += 7
                    self.recv_status = 3
        elif self.recv_status == 3:
            self.sacp_cache.append(b_data)
            ui.e_sacp_cache_data_signal.emit("{:0>2x} ".format(b_data))
            if len(self.sacp_cache) == self.need_recv_len:
                self.sacp_recv_end()


if __name__ == '__main__':
    # creat_update_packet(PACK_TYPE_J1, (0, 100), "V1.1.0", 0x8000000, "d:/my_code/tool_set/module/sacp_update.py", "./app_pack.bin")
    data = bytes([1,2,3])
    head = sacp_pack(SACP_ID_HMI, SACP_ID_CONTROLLER, 1, 2, data, len(data), 1, 0)
    print(type(head))
    print("len:", len(head))
    print(head)