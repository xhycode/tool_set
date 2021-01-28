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
        self.step_init()

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
        self.home("x")

    def home_y(self):
        self.home("Y")

    def home_z(self):
        self.home("Z")

    def home_b(self):
        self.home("B")

    def check_connect_type():
        pass

    def run(self):
        while  True:
            slef.check_connect_type()
