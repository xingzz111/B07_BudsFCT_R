#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 16:56
=====================
"""

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal, QObject
from PySide6.QtWidgets import QTableView, QWidget, QVBoxLayout


class TableController(QObject):
    def __init__(self, headers, data):
        super().__init__()
        self.model = TableModel(headers, data)
        self.view = TableView()
        self.view.setModel(self.model)
        self.model.dataChanged.connect(self.view.update)
        self.setTableData(data)

    def setTableData(self, data):
        self.model.updateData(data)


class TableModel(QAbstractTableModel):
    dataChanged = Signal()

    def __init__(self, headers, data):
        super().__init__()
        self.headers = headers
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def getData(self):
        return self._data

    def updateData(self, data):
        self._data = data
        self.dataChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(self.headers[section])
        return None


class TableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionsClickable(True)



if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    h = ["Name", "Age", "Gender"]
    d = [
        ["John", 30, "Male"],
        ["Emma", 25, "Female"],
        ["Michael", 40, "Male"]
    ]
    controller = TableController(h, d)
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(controller.view)
    widget.show()
    sys.exit(app.exec())
