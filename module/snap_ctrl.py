# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread
from module.module_base import ModuleBase
from ui import ui
import cfg
import debug

CONNECT_TYPE_PC = 0  # 电脑控制，只用串口线连接
CONNECT_TYPE_SC = 1  # 模拟屏幕控制，使用屏幕线连接

class SnapControl(QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        ModuleBase.__init__(self)
        self.line_data = ""
        self.step_init()
        self.print3d_init()
        self.cur_connect = CONNECT_TYPE_PC

    # 运动控制
    def step_init(self):
        ui.x_add.clicked.connect(self.move_x_add)
        ui.x_sub.clicked.connect(self.move_x_sub)
        ui.y_add.clicked.connect(self.move_y_add)
        ui.y_sub.clicked.connect(self.move_y_sub)
        ui.z_add.clicked.connect(self.move_z_add)
        ui.z_sub.clicked.connect(self.move_z_sub)
        ui.b_add.clicked.connect(self.move_b_add)
        ui.b_sub.clicked.connect(self.move_b_sub)
        ui.e_add.clicked.connect(self.move_e_add)
        ui.e_sub.clicked.connect(self.move_e_sub)
        ui.x_home.clicked.connect(self.home_x)
        ui.y_home.clicked.connect(self.home_y)
        ui.z_home.clicked.connect(self.home_z)
        ui.b_home.clicked.connect(self.home_b)
        ui.all_home.clicked.connect(self.home_all)
        ui.speed_unit.stateChanged.connect(self.set_speed_unit)
        # 按键颜色初始化
        ui.x_add.setStyleSheet("background-color: #008000;font-weight:bold;")
        ui.x_sub.setStyleSheet("background-color: #008000;font-weight:bold;")
        ui.y_add.setStyleSheet("background-color: #008000;font-weight:bold;")
        ui.y_sub.setStyleSheet("background-color: #008000;font-weight:bold;")
        ui.z_add.setStyleSheet("background-color: #608000;font-weight:bold;")
        ui.z_sub.setStyleSheet("background-color: #608000;font-weight:bold;")
        ui.b_add.setStyleSheet("background-color: #008080;font-weight:bold;")
        ui.b_sub.setStyleSheet("background-color: #008080;font-weight:bold;")
        ui.e_add.setStyleSheet("background-color: #509030;font-weight:bold;")
        ui.e_sub.setStyleSheet("background-color: #509030;font-weight:bold;")
        ui.x_home.setStyleSheet("background-color: #909090;font-weight:bold;")
        ui.y_home.setStyleSheet("background-color: #909090;font-weight:bold;")
        ui.z_home.setStyleSheet("background-color: #909090;font-weight:bold;")
        ui.b_home.setStyleSheet("background-color: #909090;font-weight:bold;")
        ui.all_home.setStyleSheet("background-color: #806060;font-weight:bold;")

    def set_speed_unit(self, state):
        if state:
            speed = int(ui.step_speed.displayText()) // 60
            ui.speed_unit_label.setText("速度   mm/s")
        else:
            speed = int(ui.step_speed.displayText()) * 60
            ui.speed_unit_label.setText("速度mm/min")
        ui.step_speed.setText(str(speed))

    def get_step_speed(self):
        speed = int(ui.step_speed.displayText())
        if ui.speed_unit.checkState():
            speed *= 60  # 变成mm/min
        return speed

    def wait_ack(self, timeout_ms=0):
        pass

    def get_step_mm(self):
        return ui.step_mm.value()

    def move_axis(self, axis, dir):
        mm = self.get_step_mm() * dir
        speed = self.get_step_speed()
        self.send_str("G91\r\n")
        cmd = "G0 {}{} F{}\r\n".format(axis, mm, speed)
        self.send_str(cmd)
        self.send_str("G90\r\n")
        self.wait_ack(1000)

    def move_x_add(self):
        self.move_axis("X", 1)

    def move_x_sub(self):
        self.move_axis("X", -1)

    def move_y_add(self):
        self.move_axis("Y", 1)

    def move_y_sub(self):
        self.move_axis("Y", -1)

    def move_z_add(self):
        self.move_axis("Z", 1)

    def move_z_sub(self):
        self.move_axis("Z", -1)

    def move_b_add(self):
        self.move_axis("B", 1)

    def move_b_sub(self):
        self.move_axis("B", -1)

    def move_e_add(self):
        self.move_axis("E", 1)

    def move_e_sub(self):
        self.move_axis("E", -1)

    def home(self, home_axis=''):
        cmd = "G28 {}\r\n".format(home_axis)
        self.send_str(cmd)
        self.wait_ack(1000)

    def home_all(self):
        self.home()
   
    def home_x(self):
        self.home("X")

    def home_y(self):
        self.home("Y")

    def home_z(self):
        self.home("Z")

    def home_b(self):
        self.home("B")

    # 3D头控制
    def print3d_init(self):
        ui.set_fan_0.clicked.connect(self.set_print_fan0)
        ui.set_fan_1.clicked.connect(self.set_print_fan1)
        ui.set_nozzle_temp.clicked.connect(self.set_nozzle_temp)
        ui.set_bed_temp.clicked.connect(self.set_bed_temp)

    def set_fan_power(self, index, power):
        if power > 100:
            power = 100
        if power < 0:
            power = 0
        cmd = "M106 P{} S{}".format(index, power * 255 // 100)
        self.send_str(cmd)

    def set_print_fan0(self):
        power = ui.fan_0_target.value()
        self.set_fan_power(0, power)

    def set_print_fan1(self):
        power = ui.fan_1_target.value()
        self.set_fan_power(1, power)

    def set_nozzle_temp(self):
        temp = ui.nozzle_temp_target.value()
        cmd = "M104 S{}".format(temp)
        self.send_str(cmd)

    def set_bed_temp(self):
        temp = ui.bed_temp_target.value()
        cmd = "M109 S{}".format(temp)
        self.send_str(cmd)

    def show_nozzle_temp(self, cur, target):
        ui.nozzle_temp_val.setText("{}/{}".format(cur, target))

    def show_bed_temp(self, cur, target):
        ui.bed_temp_val.setText("{}/{}".format(cur, target))

    def show_cut_switch_status(self, status):
        if status:
            ui.cut_switch_status.setText("有")
        else:
            ui.cut_switch_status.setText("无")

    def show_probe_status(self, status):
        if status:
            ui.probe_status.setText("开")
        else:
            ui.probe_status.setText("关")


    def check_connect_type(self):
        pass

    def parse(self, data):
        try:
            ch = data.decode()
        except:
            debug.err('数据编码错误')
            return
        if ch == '\n':
            debug.data(self.line_data + '\n')
            self.line_data = ''
        else:
            self.line_data += ch

    def run(self):
        while  True:
            self.check_connect_type()
