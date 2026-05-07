#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 15:31
=====================
"""

from configure.constants import GUI_CFG, ICONPATH
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
)


class BaseView(QMainWindow):
    def __init__(self, heaterView, contentView, scanView):
        super().__init__()
        self.setWindowTitle("OSSNSTester")
        self.setWindowIcon(QIcon(ICONPATH))
        mainWidget = QWidget()
        self.setCentralWidget(mainWidget)
        mainLayout = QVBoxLayout(mainWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(5)
        topLayout = QHBoxLayout()
        botLayout = QHBoxLayout()
        topLayout.addWidget(heaterView)
        botLayout.addWidget(contentView, 5)
        botLayout.addWidget(scanView, 1)
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(botLayout)
        self.set_window_center()

    def set_window_center(self):
        screen = QApplication.primaryScreen()
        wd = screen.size().width()
        hg = screen.size().height()
        self.resize(
            wd * GUI_CFG.get("screen_width", 0.9),
            hg * GUI_CFG.get("screen_height", 0.9)
        )
        size = self.geometry()
        self.move((wd - size.width()) / 2, 0)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Question', "Are you sure to quit?",
                                     QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

