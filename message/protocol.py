#!/usr/bin/env python
# -*- coding: utf-8 -*

RET_NONE = 0
RET_CHECK_FAIL = 1
RET_SUCCESS = 2

class Protocol():
  def __init__(self):
    self.recv_data = bytearray()
    self.cmd_buf = bytearray()
    self.unpack_data = bytearray()
    self.cur_cmd = bytearray()
    self.cmd_len = 0
    self.cmd_index = 0
    self.long_pack_flag = True
  
  def _push(self, data) :
    ''' data: type bytearray / bytes '''
    for it in data:
      self.recv_data.append(it)

  def get_data(self):
      '''返回已经去掉包头的数据
        类型：list, 每个元素代表一个字节的值
      '''
      return self.cur_cmd

  def unpack(self, data) :
    '''data 为单个字节数据
      返回：RET_SUCCESS  已经获取一包数据, 可以使用 get_data 获取数据
      返回：RET_CHECK_FAIL  数据解析错误
      返回：RET_NONE  还没收到完整数据
    '''
    self._push(data)
    while len(self.recv_data) > 0:
      data = self.recv_data[0]
      if len(self.recv_data) > 1:
        self.recv_data = self.recv_data[1:]
      else:
        self.recv_data = []
      index = len(self.cmd_buf)
      if index == 0 and data == 0xaa:
        self.cmd_buf.append(data)
        continue
      elif index == 1 and data != 0x55:
        self.cmd_buf = bytearray()
        continue
      elif index > 0 :
        self.cmd_buf.append(data)
        if index + 1 == 6:
          data_len_check = self.cmd_buf[2] ^ self.cmd_buf[3]
          if data_len_check != self.cmd_buf[5]:
            self.cmd_buf = bytearray()
            continue
        elif index > 7:
          data_len = (self.cmd_buf[2] << 8) | (self.cmd_buf[3])
          self.cmd_len = len(self.cmd_buf) - 8
          if data_len  == self.cmd_len :
            check = self._check_data(self.cmd_buf[8:], self.cmd_len)
            ch1 = ((check >> 8) & 0xff)
            ch2 = (check & 0xff)
            if ch1 == self.cmd_buf[6] and self.cmd_buf[7] == ch2:
              self.cur_cmd = self.cmd_buf[8:]
              self.cmd_buf = []
              return RET_SUCCESS
            else :
              self.cmd_buf = []
              return RET_CHECK_FAIL
    return RET_NONE

  @staticmethod
  def _check_data(data, len):
    checknum = 0
    if len > 0 :
      for i in range(0, (len - 1) , 2) :
        checknum += (((data[i]&0xff) << 8) | (data[i+1]&0xff))
      if len % 2 != 0:
        checknum += data[len - 1]
    while checknum > 0xffff:
      checknum = ((checknum >> 16) & 0xffff) + (checknum & 0xffff)
    checknum = ~checknum
    return checknum

  @staticmethod
  def pack(event=None, opcode=None, data=None):
    ''' 静态方法，无需定义即可使用
        data: 待打包的数据, 数据类型 bytearray
        返回: 打包后的数据
    '''
    cmd = bytearray([0xaa, 0x55, 0, 0, 0, 0, 0, 0])
    if event is not None:
      cmd.append(event)
    if opcode is not None:
      cmd.append(opcode)
    if data is not None:
      for i in range(len(data)):
        cmd.append(data[i])
    data_len = len(cmd) - 8
    cmd[2] = (data_len >> 8) & 0xff
    cmd[3] = data_len & 0xff
    cmd[5] = cmd[2]^cmd[3]
    check = Protocol._check_data(cmd[8:], data_len)
    cmd[6] = (check >> 8) & 0xff
    cmd[7] = check & 0xff
    return cmd


if __name__ == "__main__":
    pack = Protocol()
    cmd = pack.pack(0xaa, 0x1, bytes([0x1, 0x2]))
    print(bytes.hex(bytes(cmd)))