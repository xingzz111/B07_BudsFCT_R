#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PySide6.QtWidgets import QTableView, QFrame, QAbstractScrollArea, QAbstractItemView, QApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView


class KTableView(QTableView):
    def __init__(self, parent=None):
        super(KTableView, self).__init__(parent)
        self.all_info = list()
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(26)
        self.setAlternatingRowColors(True)

    def set_columns_width(self, width_list=None):
        if width_list is None:
            width_list = [80, 140, 220, 50, 50, 50]
        for i in range(len(width_list)):
            self.setColumnWidth(i, width_list[i])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = KTableView()
    view.set_columns_width()
    view.show()
    view.setGeometry(500, 50, 600, 480)
    sys.exit(app.exec())
