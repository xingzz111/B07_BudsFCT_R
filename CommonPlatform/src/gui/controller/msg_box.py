#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
from PySide6.QtCore import Qt, QObject
from PySide6.QtWidgets import QApplication, QMessageBox


class MessageBox(QObject):
    def __init__(self):
        super(StartBox, self).__init__()

    @staticmethod
    def show(info):
        screen = QApplication.primaryScreen()
        wd = screen.size().width()
        message_box = QMessageBox()
        message_box.setWindowFlags(Qt.WindowStaysOnTopHint)
        message_box.setModal(True)
        message_box.move(wd/3.5, 0)
        QMessageBox.critical(message_box, "Start Fail", info)
        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MessageBox.show('PRMTester is Running now!')
    sys.exit(1)
