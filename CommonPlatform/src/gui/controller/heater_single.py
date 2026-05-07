#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 16:53
=====================
"""
from rtLib import levels
from configure import constants
from rtLib.common import print_with_time
from configure.constants import State
from gui.controller.groupstatus import GroupController
from gui.resources.style import Font, Color
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer, Qt, QSize, QObject
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGroupBox


class HeaderController(QObject):
    def __init__(self, signalBox=None):
        super().__init__()
        self._signalBox = signalBox
        self._runTime = 0.0
        self.signatureStatus = True
        self.testPlanC = GroupController()
        self.view = HeaderView(self.testPlanC.view)
        self._timer = QTimer()
        self._timer.timeout.connect(self.counter_timer)
        self.view.updateStatus(State.IDLE)

    def messageBox(self, msg, level=levels.INFO):
        if self._signalBox:
            self._signalBox.emit(msg, level)
        else:
            print_with_time(msg)

    def updateSn(self, sn):
        self.view.labSn.setText(f"SN:{sn}")

    def startTest(self):
        self.testPlanC.clean()
        self.start_header_timer()
        self.view.updateStatus(State.RUNNING)
        self.testPlanC.sequence_start(-1)

    def endTest(self, result):
        state = State.PASS if result else State.FAIL
        self.stop_header_timer()
        self.view.updateStatus(state)
        self._mlbSn = None

    def counter_timer(self):
        self._runTime = round(self._runTime + 0.1, 1)
        self.view.labCounting.setText(str(self._runTime) + "s")

    def start_header_timer(self):
        self._runTime = 0.0
        self._timer.start(100)

    def stop_header_timer(self):
        self._timer.stop()

    def updateSecurity(self, flag):
        self.view.updateSecurity(flag)
        self.signatureStatus = flag


class HeaderView(QWidget):
    def __init__(self, tabView):
        super(HeaderView, self).__init__()
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.headerGroup = QGroupBox(self)
        self.headerGroup.setContentsMargins(2, 2, 2, 2)
        subLayout = QVBoxLayout(self.headerGroup)
        topLayout = QHBoxLayout()
        topLayout.setContentsMargins(0, 0, 0, 0)
        topLayout.setSpacing(100)
        sub1TopLayout = QVBoxLayout()
        sub1TopLayout.setContentsMargins(0, 0, 0, 0)
        sub1TopLayout.setSpacing(1)
        sub2TopLayout = QVBoxLayout()
        sub2TopLayout.setContentsMargins(0, 0, 0, 0)
        sub2TopLayout.setSpacing(1)
        sub3TopLayout = QVBoxLayout()
        sub3TopLayout.setContentsMargins(0, 0, 0, 0)
        sub3TopLayout.setSpacing(1)
        bottLayout = QHBoxLayout()
        bottLayout.setContentsMargins(0, 0, 0, 0)
        self.labSn = QLabel()
        self.labCounting = QLabel()
        self.labCounting.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.labSecurity = QLabel()
        self.labSecurity.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.labLogo = QLabel()
        sub1TopLayout.addWidget(self.labSn)
        sub2TopLayout.addWidget(self.labSecurity)
        sub2TopLayout.addWidget(self.labCounting)
        sub3TopLayout.addWidget(self.labLogo)

        topLayout.addLayout(sub1TopLayout)
        topLayout.addLayout(sub2TopLayout)
        topLayout.addLayout(sub3TopLayout)

        bottLayout.addWidget(tabView)
        subLayout.addLayout(topLayout)
        subLayout.addLayout(bottLayout)

        self.mainLayout.addWidget(self.headerGroup)
        self.setupFormat()

    def setupFormat(self):
        # self.headerGroup.setTitle("Group Status")
        pixMapLogo = QPixmap(constants.LogoPng)
        pixMapLogo = pixMapLogo.scaled(QSize(300, 50), Qt.KeepAspectRatio)
        self.labLogo.setPixmap(pixMapLogo)
        self.labLogo.setAlignment(Qt.AlignRight)
        self.labSn.setText(f"SN:")
        self.labSn.setFixedSize(360, 50)
        self.labSn.setFont(Font.FONT_24)
        self.labSn.setStyleSheet(Color.bg_green + Color.black)
        self.labCounting.setText("0.0s")
        self.labCounting.setFont(Font.FONT_24)
        self.labCounting.setStyleSheet(Color.black)
        self.updateSecurity(True)

    def updateStatus(self, status):
        if status == State.IDLE:
            self.labSn.setStyleSheet(Color.bg_orange + Color.black)
        elif status == State.RUNNING:
            self.labSn.setStyleSheet(Color.bg_blue + Color.black)
        elif status == State.PASS:
            self.labSn.setStyleSheet(Color.bg_green + Color.black)
        else:
            self.labSn.setStyleSheet(Color.bg_red + Color.black)

    def updateSecurity(self, state: bool):
        if state:
            pixMapGLock = QPixmap(constants.GLockPng)
            pixMapGLock = pixMapGLock.scaled(QSize(45, 45), Qt.KeepAspectRatio)
            self.labSecurity.setPixmap(pixMapGLock)
        else:
            pixMapRLock = QPixmap(constants.RLockPng)
            pixMapRLock = pixMapRLock.scaled(QSize(45, 45), Qt.KeepAspectRatio)
            self.labSecurity.setPixmap(pixMapRLock)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ui = HeaderController()
    ui.view.show()
    ui.start_header_timer()
    sys.exit(app.exec())
