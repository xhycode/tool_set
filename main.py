# -*- coding: utf-8 -*-
import sys
from control import Control
from ui import ui

if __name__ == '__main__':
    ui.show()
    ctrl = Control()
    sys.exit(ui.app.exec_())
