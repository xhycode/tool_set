# tool_set

#### 介绍
    将常用的通信如(串口、TCP)等集成到一个工具上。以及其它的工具如串口示波器等

#### 软件架构
目录说明
- root                      ->> 根目录
    * main.py                   ->> 程序入口文件
    * control.py                ->> 控制程序工作流
    * debug.py                  ->> 调试信息显示到调试窗口
    - ui                    ->> 界面相关模块
        * __init__.py           ->> 里边的 ui 变量可以用来访问所有的小部件
        * global.py             ->> 将窗口部件封装一层，并添加信号提供外出使用
        * main_window.py        ->> 使用 pyuic5 -o .\main_window.py .\main_window.ui 生成的文件。不能在里边添加自己的代码，重新生生成会覆盖
        * main_window.ui        ->> Qt Designer 工程文件
    - module                ->> 功能相关的模块
        * __init__.py           ->> 管理模块的切换
        * data_display.py       ->> 数据显示面板模块
        * wavefrom.py           ->> 示波器显示模块
        * module.base.py        ->> 模块通用的接口，所有模块继承这个类，方便统一处理
    - message               ->> 消息管理
        * __init__.py           ->> 负责各种通信方式的切换
        * serial_tool.py        ->> 串口通信模块


#### 安装教程

1.  xxxx
2.  xxxx
3.  xxxx

#### 使用说明

1.  Qt Designer版本：5.11.1  https://build-system.fman.io/qt-designer-download
2.  小部件使用：https://doc.qt.io/qtforpython/PySide2/QtWidgets/
3.  python 测试过的版本： 3.8.2
4.  测试过的系统： win10
5.  依赖库：
        - windows
            * pip install serial -i https://pypi.douban.com/simple
            * pip install configobj -i https://pypi.douban.com/simple
            * pip install pyqt5 -i https://pypi.douban.com/simple
            * pip install pyqtgraph -i https://pypi.douban.com/simple
            * pip install pyinstaller  # 打包成exe
             pyinstaller --onefile -w --icon=mao.ico .\main.py
        - linux
            * pip3 install serial -i https://pypi.douban.com/simple
            * pip3 install pyserial -i https://pypi.douban.com/simple
            * pip3 install configobj -i https://pypi.douban.com/simple
            * pip3 install pyqtgraph -i https://pypi.douban.com/simple
            * sudo apt-get install python3-pyqt5
            * alias pyuic5="python3 -m PyQt5.uic.pyuic"  # 添加pyuic5到快捷方式，就可以直接用了

#### 版本说明

- V1.0.0
    * 完成软件的基本框架
    * 串口收发功能
    * 数据 字符串/ hex 发送功能
    * 数据显示方式支持全局 hex 显示切换
    * 自动发送功能
    * 可设置字体大小及字体选择


