#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 16:53
=====================
"""
import time
from rtrpcLib import levels
from configure import constants
from rtrpcLib.common import print_with_time
from configure.constants import State
from gui.resources.style import Font, Color
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer, Qt, QSize, QObject
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget


class HeaderController(QObject):
    def __init__(self, signalBox=None):
        super().__init__()
        self._signalBox = signalBox
        self._runTime = 0.0
        self.signatureStatus = True
        self.view = HeaderView()
        self._timer = QTimer()
        self._timer.timeout.connect(self.counter_timer)

    def messageBox(self, msg, level=levels.INFO):
        if self._signalBox:
            self._signalBox.emit(msg, level)
        else:
            print_with_time(msg)

    def startTest(self):
        self.start_header_timer()

    def endTest(self, result):
        self.stop_header_timer()

    def counter_timer(self):
        # self._runTime =
        self.view.labCounting.setText(str(round(time.time() - self._runTime, 2)) + "s")

    def start_header_timer(self):
        if self._timer.isActive():
            return
        self._runTime = time.time()
        self._timer.start(100)

    def stop_header_timer(self):
        self._timer.stop()

    def updateProjectInfo(self, Project:str, version:str):
        self.view.labProjectInfo.setText(Project.strip().upper())
        self.view.labVersionInfo.setText(version.strip())

    def updateSecurity(self, state: bool):
        self.signatureStatus = state
        if state:
            self.view.labSecurity.setPixmap(self.view.pixMapGLock)
        else:
            self.view.labSecurity.setPixmap(self.view.pixMapRLock)


class HeaderView(QWidget):
    def __init__(self):
        super(HeaderView, self).__init__()
        self.pixMapGLock = None
        self.pixMapRLock = None
        self.labProjectInfo = QLabel()
        self.labVersionInfo = QLabel()
        self.labCounting = QLabel()
        self.labSecurity = QLabel()
        self.labPDCA = QLabel()
        self.labLogo = QLabel()
        self.layoutWidgets()
        self.setupFormat()

    def layoutWidgets(self):
        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(5, 5, 5, 5)
        mainLayout.setSpacing(0)
        sub1Layout = QVBoxLayout()
        sub1Layout.setContentsMargins(0, 0, 0, 0)
        sub2Layout = QVBoxLayout()
        sub2Layout.setContentsMargins(5, 5, 5, 5)
        sub2Layout.setSpacing(10)
        sub3Layout = QVBoxLayout()
        sub3Layout.setContentsMargins(0, 0, 0, 0)
        sub4Layout = QVBoxLayout()
        sub3Layout.setContentsMargins(0, 0, 0, 0)
        sub1Layout.addWidget(self.labProjectInfo)
        sub1Layout.addWidget(self.labVersionInfo)
        sub2Layout.addWidget(self.labSecurity)
        sub2Layout.addWidget(self.labCounting)
        sub3Layout.addWidget(self.labLogo)
        sub4Layout.addWidget(self.labPDCA)
        mainLayout.addLayout(sub1Layout)
        mainLayout.addLayout(sub2Layout)
        mainLayout.addLayout(sub4Layout)
        mainLayout.addLayout(sub3Layout)
        self.setLayout(mainLayout)

    def setupFormat(self):
        pixMapLogo = QPixmap(constants.LogoPng)
        pixMapLogo = pixMapLogo.scaled(QSize(400, 75), Qt.KeepAspectRatio)
        pixMapGLock = QPixmap(constants.GLockPng)
        self.pixMapGLock = pixMapGLock.scaled(QSize(45, 45), Qt.KeepAspectRatio)
        pixMapRLock = QPixmap(constants.RLockPng)
        self.pixMapRLock = pixMapRLock.scaled(QSize(45, 45), Qt.KeepAspectRatio)
        self.labSecurity.setPixmap(self.pixMapGLock)
        self.labProjectInfo.setText(f"{constants.PROJECT}")
        # self.labProjectInfo.setFixedSize(360, 50)
        self.labProjectInfo.setFont(Font.FONT_32)
        self.labProjectInfo.setStyleSheet(Color.blue)
        self.labProjectInfo.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.labVersionInfo.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        self.labCounting.setText("0.0s")
        self.labCounting.setFont(Font.FONT_26)
        self.labCounting.setStyleSheet(Color.black)
        self.labCounting.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.labSecurity.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.labPDCA.setText("NOMES")
        self.labPDCA.setStyleSheet(
            """
            QLabel {
                background-color: yellow;
                font-size: 24px;
                padding: 10px;
            }
            """
        )
        self.enable_pdca(False)
        self.labPDCA.setAlignment(Qt.AlignCenter)
        self.labLogo.setPixmap(pixMapLogo)
        self.labLogo.setAlignment(Qt.AlignRight)

    def enable_pdca(self, enable=True):
        if not enable:
            self.labPDCA.show()
        else:
            self.labPDCA.hide()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ui = HeaderController()
    ui.view.show()
    ui.start_header_timer()
    sys.exit(app.exec())
