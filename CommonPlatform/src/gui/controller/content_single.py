#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 16:56
=====================
"""

from rtLib import levels
from rtLib.common import print_with_time
from configure.constants import State
from gui.resources.style import Font, Color
from PySide6.QtCore import Qt, QObject
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QWidget


class ContentController(QObject):
    def __init__(self, signalBox=None):
        super().__init__()
        self._signalBox = signalBox
        self.view = ContentView()
        self.changeMode(State.IDLE)

    def messageBox(self, msg, level=levels.INFO):
        if self._signalBox:
            self._signalBox.emit(msg, level)
        else:
            print_with_time(msg)

    def startTest(self):
        self.changeMode(State.RUNNING)

    def endTest(self, result):
        state = State.PASS if result else State.FAIL
        self.changeMode(state)

    def changeMode(self, state):
        if state == State.IDLE:
            self.view.labSatus.setText('IDLE')
            self.view.labSatus.setStyleSheet(Color.bg_orange + Color.white)
        elif state == State.RUNNING:
            self.view.labSatus.setText('RUNNING')
            self.view.labSatus.setStyleSheet(Color.bg_blue + Color.white)
        elif state == State.PASS:
            self.view.labSatus.setText('PASS')
            self.view.labSatus.setStyleSheet(Color.bg_green + Color.white)
        else:
            self.view.labSatus.setText('FAIL')
            self.view.labSatus.setStyleSheet(Color.bg_red + Color.white)


class ContentView(QWidget):
    def __init__(self):
        super(ContentView, self).__init__()
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.statusGroup = QGroupBox(self)
        self.labSatus = QLabel()

        subMainLayout = QHBoxLayout(self.statusGroup)
        subMainLayout.setContentsMargins(0, 0, 0, 0)
        subMainLayout.setSpacing(0)
        leftLayout = QVBoxLayout()
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.setSpacing(0)
        leftLayout.addWidget(self.labSatus)
        subMainLayout.addLayout(leftLayout)

        self.mainLayout.addWidget(self.statusGroup)
        self.setupFormat()

    def setupFormat(self):
        self.statusGroup.setTitle("Overall Status")
        # self.labSatus.setFixedSize(600, 300)
        self.labSatus.setAlignment(Qt.AlignCenter)
        self.labSatus.setText("IDLE")
        self.labSatus.setFont(Font.FONT_45)
        self.labSatus.setStyleSheet(Color.bg_orange + Color.white)


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ui = ContentController()
    ui.view.show()
    # ui.start_header_timer()
    sys.exit(app.exec())
