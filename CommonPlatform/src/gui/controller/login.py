#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import base64
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QDialog, QMessageBox
from PySide6.QtCore import QObject


class LoginController(QObject):
    def __init__(self):
        super(LoginController, self).__init__()

    @staticmethod
    def get_password():
        login_dialog = QDialog()
        login_dialog.setWindowTitle("Authentication")

        main_layout = QVBoxLayout()
        lbl_pwd = QLabel('password:')
        line_pwd = QLineEdit()
        line_pwd.setEchoMode(QLineEdit.Password)
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(lbl_pwd)
        pwd_layout.addWidget(line_pwd)
        btn_layout = QHBoxLayout()

        btn_cancel = QPushButton('Cancel')
        btn_ok = QPushButton('OK')
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        main_layout.addLayout(pwd_layout)
        main_layout.addLayout(btn_layout)
        main_layout.setContentsMargins(5, 1, 5, 5)
        main_layout.setSpacing(5)
        login_dialog.setLayout(main_layout)
        login_dialog.setFixedSize(250, 100)
        login_dialog.setModal(True)
        login_dialog.setLayout(main_layout)
        btn_ok.clicked.connect(login_dialog.accept)
        btn_ok.setDefault(True)
        btn_cancel.clicked.connect(login_dialog.reject)

        if login_dialog.exec_() == QDialog.Accepted:
            #rtTech123
            today = datetime.date.today()
            str_today = today.strftime("%Y%m%d")
            print(str_today.encode())
            print(line_pwd.text().encode())
            if base64.encodebytes('{}'.format(str_today).encode()) == base64.encodebytes(line_pwd.text().encode()):
                return True
            else:
                QMessageBox.critical(QMessageBox(), "WRONG PASSWORD",
                                     "WRONG PASSWORD!!!\n",
                                     buttons=QMessageBox.Yes)
                return False
