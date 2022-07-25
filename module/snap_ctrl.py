# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread
from module.module_base import ModuleBase
from module.sacp_update import SnapUpdateTool
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer
from ui import ui
import time
import os
import cfg
import debug

CONNECT_TYPE_PC = 0  # 电脑控制，只用串口线连接
CONNECT_TYPE_SC = 1  # 模拟屏幕控制，使用屏幕线连接

STEP_SET_MM = (0.05, 0.1, 0.5, 1, 5, 10, 50)

MACHINE_TYPE_LIST = ["snapmaker 2.0"]

PRINT_STATUS_IDLE = 0
PRINT_STATUS_WORK = 1
PRINT_STATUS_PAUSE = 2

snapmaker_2_exception_info = {
    #  [异常名称, 异常原因， 检测时机， 检测修复方法]
    0:["上电时检测不到执行头", "1.未连接执行头,2.线未连接好", "上电初始化时", "上电初始化时"],
    1:["无直线模组", "1.未检测到任何执行模组,2.直线模组插错端口,3.连接线断开 ", "上电初始化时", "1.连接直线模组,2.检查直线模组是否连接正确"],
    2:["热床端口损坏", "热床加热控制电路损坏", "上电后一直检测", "这个用户端没办法修复，需寄回售后"],
    3:["断料", "断料开关汇报没料,并继续挤出5mm之后", "工作中", "续料即可"],
    4:["参数丢失", "1.烧固件后第一次读取参数时会出现此情况,2.使用期间如果flash有坏块,也会出现此情况，且此情况为永久损坏，无法修复", "上电加载配置时", "恢复出厂设定"],
    5:["执行头丢失", "待机/暂停/工作过程中执行头突然丢失，原因:1.连接线未插好2.执行头死机", "枚举到执行头之后", "断电后:1.检查连接是否插好,2.重新拔插连接线"],
    6:["掉电", "220V突然断电", "检测掉电保存的数据", ""],
    7:["挤出头加热失败", "在指定时间内温升未达标", "加热过程中", "断电后，检查打印头热端是否安装好"],
    8:["热床加热失败", "在指定时间内温升未达标", "加热过程中", "断电后，检查热床热敏电阻是否脱落"],
    9:["挤出头温度跑飞", "当前温度大于目标温度，且在指定时间内没回到目标温度", "加热过程或者稳定之后", "低概率问题，断电后：检查挤出头热端是否完好"],
    10:["热床温度跑飞", "当前温度大于目标温度，且在指定时间内没回到目标温度", "加热过程或者稳定之后", "低概率问题，断电后：检查热床的连接线是否完好"],
    11:["挤出头热敏电阻异常", "温度数值小于0或者大于500", "待机或工作中", "断电后：检查挤出头热端是否完好"],
    12:["热床热敏电阻异常", "温度数值小于0", "待机或工作中", "断电后：检查热床热敏电阻/连接线是否完好"],
    13:["直线模组丢失", "在运行过程中某根直线模组丢失", "目前未支持此检测", "断电后：检查直线模组是否插好"],
    14:["挤出头温度超过最大限值", "加热失控，导致温度大于 290℃", "全程", "断电后：检查挤出头热端是否连接好，是否有短路"],
    15:["热床超过最大限值", "加热失控,导致温度大于130℃", "全程", "断电后：检查热床的连接线是否完好，是否有短路"],
    16:["挤出头温度超过二次限制", "无法关闭加热,导致温度大于300 ℃", "全程", "断电后：检查挤出头热端是否连接好，是否有短路"],
    17:["热床温度超过二次限制", "无法关闭加热，导致温度大于 135℃", "全程", "断电后：检查热床的连接线是否完好，是否有短路"],
    18:["挤出头温度在开启加热后温度不上升，或者加热过程中温度骤降", "1.温度不上升：热敏电阻已经脱落：导致加热过程中检测不到热源温度,2.温度骤降：热敏电阻在加热过程中脱落，导致温度骤降", "开启加热后", "断电后：检查挤出头热端的热敏电阻是否脱落"],
    19:["热床温度在开启加热后温度不上升，或者加热过程中温度骤降", "1.温度不上升：热敏电阻已经脱落：导致加热过程中检测不到热源温度,2.温度骤降：热敏电阻在加热过程中脱落，导致温度骤降", "开启加热后", "断电后：检查热床的热敏电阻是否脱落"],
    20:["检测不出机型", "根据拿到的直线模组数量和长度,无法判断出当前机型。在XYZ接错的时候极可能出现", "初始化直线模组的过程中", "1.检查直线模组是否按照规定连接到正确端口,2.中大型机器,检查1拖2的连接是否正确"],
    21:["门打开", "外罩已连接且已经使能门检测的情况下，检测到门打开了", "", ""],
    22:["掉电检测引脚异常", "在220V供电正常的情况下,电源盒输出掉电信号", "", ""],
    23:["某根轴的直线模组导程错误", "tmc驱动的直线模组,z轴的直线模组与x y轴的直线模组不能混用", "", "调换各轴的直线模组"],
    24:["同一台机器有两种驱动芯片的直线模组", "4988和tmc2209驱动的直线模组混用了", "", "更换同一驱动芯片的直线模组"],
    31:["未知异常", "", "", "联系售后"]
}

class SnapControl(QThread, ModuleBase):
    def __init__(self):
        super().__init__()
        ModuleBase.__init__(self)
        self.line_data = ""
        self.step_init()
        self.print3d_init()
        self.base_ctrl_init()
        self.print_work_init()
        self.exception_code_parsing_init()
        self.update_tool = SnapUpdateTool(self.send_bytes)
        self.cur_connect = CONNECT_TYPE_PC
        ui.snapmaker_tool.setCurrentIndex(0)

    def print_work_init(self):
        self.print_work_status = PRINT_STATUS_IDLE
        self.print_line_num = 0
        self.print_restart_times = 0
        self.print_cmd = ["", "", ""]
        ui.open_print_file.clicked.connect(self.open_print_file_event)
        ui.print_start.clicked.connect(self.start_print_event)
        ui.print_stop.clicked.connect(self.stop_print_event)
        ui.print_manual_continue.clicked.connect(self.print_manual_continue_event)
        self.print_file_name = cfg.get(cfg.PRINT_FILE_NAME, '')
        ui.print_file_name.setText(self.print_file_name)
        self.print_info_show_timer = QTimer()
        self.print_info_show_timer.timeout.connect(self.renew_print_info)

    def is_print_work(self):
        return self.print_work_status == PRINT_STATUS_WORK

    def open_print_file_event(self):
        if self.print_work_status != PRINT_STATUS_IDLE:
            debug.err("工作状态禁止操作")
            return
        self.print_file_name=QFileDialog.getOpenFileName(ui)[0]
        self.print_line_num = 0
        cfg.set(cfg.PRINT_FILE_NAME, self.print_file_name)
        if self.print_file_name == '':
            debug.err("没选择文件文件")
            return
        ui.print_file_name.setText(self.print_file_name)

    def start_print_work(self):
        if os.path.exists(self.print_file_name):
            debug.info("加载文件："+self.print_file_name)
            with open(self.print_file_name) as gcode:
                self.print_file_lines = gcode.readlines()
                self.print_total_lines = len(self.print_file_lines)
                gcode.close()
                debug.info("gcode总行数:"+str(self.print_total_lines))
            self.print_cmd = ["", "", ""]
            self.start_work_time = time.time()
            ui.print_start_btn_status_signal.emit("暂停", "background-color: #008000;font-weight:bold;")
            self.print_work_status = PRINT_STATUS_WORK
            self.print_line_num = 0
            self.print_restart_times = 0
            self.send_file_gcode()
            debug.info("开始打印工作")
            self.print_info_show_timer.start(0)
        else:
            debug.err("文件路径错误")

    def pause_print_work(self):
        ui.print_start_btn_status_signal.emit("继续", "background-color: #ffce45;font-weight:bold;")
        self.print_work_status = PRINT_STATUS_PAUSE
        debug.info("暂停打印工作")

    def recover_print_work(self):
        ui.print_start_btn_status_signal.emit("暂停", "background-color: #008000;font-weight:bold;")
        self.print_work_status = PRINT_STATUS_WORK
        debug.info("恢复打印工作")
        self.send_file_gcode()

    def start_print_event(self):
        if self.print_work_status == PRINT_STATUS_IDLE:
            self.start_print_work()
        elif self.print_work_status == PRINT_STATUS_WORK:
            self.pause_print_work()
        elif self.print_work_status == PRINT_STATUS_PAUSE:
            self.recover_print_work()

    def stop_print_event(self):
        if self.print_work_status != PRINT_STATUS_IDLE:
            self.print_file_lines = None
            ui.print_start_btn_status_signal.emit("开始", "background-color: #f0f0f0;font-weight:bold;")
            debug.info("停止打印")
            self.print_work_status = PRINT_STATUS_IDLE

    def print_manual_continue_event(self):
        debug.err("这个功能还没有实现")

    def renew_print_info(self):
        ui.show_print_time_signal.emit(self.start_work_time)
        ui.show_print_cmd_signal.emit(self.print_cmd)
        ui.show_print_file_line_num_signal.emit(self.print_line_num, self.print_total_lines)
        ui.print_restart_times_signal.emit(self.print_restart_times)
        if self.print_work_status != PRINT_STATUS_IDLE:
            self.print_info_show_timer.start(500)
        else:
            self.print_info_show_timer.stop()

    def send_file_gcode(self):
        if self.print_work_status == PRINT_STATUS_WORK and self.print_file_lines:
            while True:
                if self.print_line_num < self.print_total_lines:
                    cmd = self.print_file_lines[self.print_line_num].lstrip()
                    if len(cmd) <= 1 or len(cmd) > 96 or cmd[0] == ';':
                        self.print_line_num += 1
                    else:
                        self.send_str(cmd)
                        self.print_cmd = self.print_cmd[1:]
                        self.print_cmd.append(cmd)
                        self.print_line_num += 1
                        break
                else:
                    debug.info("打印结束")
                    if ui.print_auto_restart.checkState():
                        self.print_line_num = 0
                        self.print_restart_times += 1
                        debug.info("重新开始打印")
                        continue
                    else:
                        # self.send_str("G28\r\n")
                        self.print_cmd = self.print_cmd[1:]
                        self.print_cmd.append("打印结束")
                        self.stop_print_event()
                    break

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
        for i , mm in enumerate(STEP_SET_MM):
            step_btton = getattr(ui, 'step_set_' + str(i + 1))  # 设置运动距离按钮
            fun = getattr(self, 'step_set_button' + str(i + 1))  # 触发事件函数
            step_btton.clicked.connect(fun)
            step_btton.setText(f'{mm}')
        ui.speed_unit.stateChanged.connect(self.set_speed_unit)
        ui.nozzle_temp_set.clicked.connect(self.set_nozzle_temp)
        ui.nozzle_2_temp_set.clicked.connect(self.set_nozzle_2_temp)
        ui.bed_temp_set.clicked.connect(self.set_bed_temp)
        ui.nozzle_temp_close.clicked.connect(self.close_nozzle_temp)
        ui.nozzle_2_temp_close.clicked.connect(self.close_nozzle_2_temp)
        ui.bed_temp_close.clicked.connect(self.close_bed_temp)
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

    def base_ctrl_init(self):
        ui.b_change_t0.clicked.connect(self.change_to_t0)
        ui.b_change_t1.clicked.connect(self.change_to_t1)
        ui.b_print_mode_full.clicked.connect(self.change_mode_to_full)
        ui.b_print_mode_back.clicked.connect(self.change_mode_to_back)
        ui.b_print_mode_duplication.clicked.connect(self.change_mode_to_duplication)
        ui.b_print_mode_mirror.clicked.connect(self.change_mode_to_mirror)
        ui.b_reboot.clicked.connect(self.reboot)
        ui.b_factory_reset.clicked.connect(self.factory_reset)

    def exception_code_parsing_init(self):
        ui.c_machine_type.addItems(MACHINE_TYPE_LIST)
        ui.b_exception_code_parse.clicked.connect(self.exception_code_parsing)

    def exception_code_parsing(self):
        code = ui.exception_code_input.value()
        ui.e_exception_code_win.clear()
        err_info = ""
        for i in range(32):
            if code & (1 << i):
                e = snapmaker_2_exception_info.get(i)
                if e:
                    err_info += "错误码:{:}\n    异常名称:{:}\n    异常原因:{:}\n    检测时机:{:}\n    检测修复方法:{:}\n\n".format(
                        hex(1<<i), e[0], e[1], e[2],  e[3]
                    )
        ui.e_exception_code_win.setText(err_info)

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
        cmd = "G1 {}{} F{}\r\n".format(axis, mm, speed)
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

    def step_set_button1(self):
        ui.step_mm.setValue(STEP_SET_MM[0])

    def step_set_button2(self):
        ui.step_mm.setValue(STEP_SET_MM[1])

    def step_set_button3(self):
        ui.step_mm.setValue(STEP_SET_MM[2])

    def step_set_button4(self):
        ui.step_mm.setValue(STEP_SET_MM[3])

    def step_set_button5(self):
        ui.step_mm.setValue(STEP_SET_MM[4])

    def step_set_button6(self):
        ui.step_mm.setValue(STEP_SET_MM[5])

    def step_set_button7(self):
        ui.step_mm.setValue(STEP_SET_MM[6])

    def set_nozzle_temp(self):
        temp = ui.nozzle_temp_edit.value()
        cmd = "M104 T0 S{}\r\n".format(temp)
        self.send_str(cmd)
        self.send_str("M105\r\n")

    def set_nozzle_2_temp(self):
        temp = ui.nozzle_temp_edit.value()
        cmd = "M104 T1 S{}\r\n".format(temp)
        self.send_str(cmd)
        self.send_str("M105\r\n")

    def set_bed_temp(self):
        temp = ui.bed_temp_edit.value()
        cmd = "M140 S{}\r\n".format(temp)
        self.send_str(cmd)
        self.send_str("M105\r\n")

    def close_nozzle_temp(self):
        self.send_str("M104 T0 S0\r\n")
        self.send_str("M105\r\n")

    def close_nozzle_2_temp(self):
        self.send_str("M104 T1 S0\r\n")
        self.send_str("M105\r\n")

    def close_bed_temp(self):
        self.send_str( "M140 S0\r\n")
        self.send_str("M105\r\n")

    def change_to_t0(self):
        cmd = "T0\r\n"
        self.send_str(cmd)

    def change_to_t1(self):
        cmd = "T1\r\n"
        self.send_str(cmd)

    def change_mode_to_full(self):
        cmd = "M605 S0 B0\r\n"
        self.send_str(cmd)

    def change_mode_to_back(self):
        cmd = "M605 S0 B1\r\n"
        self.send_str(cmd)

    def change_mode_to_duplication(self):
        cmd = "M605 S2 B0\r\n"
        self.send_str(cmd)

    def change_mode_to_mirror(self):
        cmd = "M605 S3 B0\r\n"
        self.send_str(cmd)

    def reboot(self):
        cmd = "M1999\r\n"
        self.send_str(cmd)

    def factory_reset(self):
        cmd = "M502\r\n"
        self.send_str(cmd)
        cmd = "M500\r\n"
        self.send_str(cmd)

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

    # def set_nozzle_temp(self):
    #     temp = ui.nozzle_temp_target.value()
    #     cmd = "M104 S{}".format(temp)
    #     self.send_str(cmd)

    # def set_bed_temp(self):
    #     temp = ui.bed_temp_target.value()
    #     cmd = "M109 S{}".format(temp)
    #     self.send_str(cmd)

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

    def gcode_parse(self, data):
        try:
            ch = data.decode()
        except:
            debug.err('数据编码错误')
            return
        self.line_data += ch
        if ch == '\n':
            debug.data(self.line_data)
            if self.print_work_status == PRINT_STATUS_WORK:
                if "ok" in self.line_data:
                    self.send_file_gcode()
                    if len(self.line_data) > 4:
                        ui.e_recv_signal.emit(self.line_data)
                else:
                    ui.e_recv_signal.emit(self.line_data)
            self.line_data = ''

    def sacp_parse(self, data):
        for d in data:
            self.update_tool.sacp_parse(d)

    def parse(self, data):
        index = ui.snapmaker_tool.currentIndex()
        if index == 2 or index == 3:
            self.sacp_parse(data)
        else:
            self.gcode_parse(data)

    def run(self):
        while  True:
            self.check_connect_type()
