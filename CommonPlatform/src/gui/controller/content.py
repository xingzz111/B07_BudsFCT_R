#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 16:56
=====================
"""

from rtrpcLib import levels
from rtrpcLib.common import print_with_time
from gui.controller.testplan import TestPlanController
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QHBoxLayout, QWidget


class ContentController(QObject):
    def __init__(self, signalBox=None):
        super().__init__()
        self._signalBox = signalBox
        self.testPlanC = TestPlanController()
        self.view = ContentView(self.testPlanC.view)

    def messageBox(self, msg, level=levels.INFO):
        if self._signalBox:
            self._signalBox.emit(msg, level)
        else:
            print_with_time(msg)

    def startTest(self):
        self.testPlanC.flushTab()

    def endTest(self, result):
        pass


class ContentView(QWidget):
    def __init__(self, tpView):
        super(ContentView, self).__init__()
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.tpView = tpView
        self.mainLayout.addWidget(self.tpView)


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ui = ContentController()
    ui.view.show()
    sys.exit(app.exec())
