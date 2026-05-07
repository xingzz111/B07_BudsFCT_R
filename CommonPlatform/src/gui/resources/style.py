#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 17:15
=====================
"""

from PySide6.QtGui import QFont

FONT_STYLE = "Arial"


class Font(QFont):
    FONT_10 = QFont(FONT_STYLE, 10)
    FONT_10_BOLD = QFont(FONT_STYLE, 10, QFont.Bold)
    FONT_12 = QFont(FONT_STYLE, 12)
    FONT_12_BOLD = QFont(FONT_STYLE, 12, QFont.Bold)
    FONT_14 = QFont(FONT_STYLE, 14)
    FONT_14_BOLD = QFont(FONT_STYLE, 14, QFont.Bold)
    FONT_16 = QFont(FONT_STYLE, 16)
    FONT_16_BOLD = QFont(FONT_STYLE, 16, QFont.Bold)

    FONT_18 = QFont(FONT_STYLE, 18)
    FONT_18_BOLD = QFont(FONT_STYLE, 18, QFont.Bold)

    FONT_20 = QFont(FONT_STYLE, 20)
    FONT_20_BOLD = QFont(FONT_STYLE, 20, QFont.Bold)

    FONT_22 = QFont(FONT_STYLE, 22)
    FONT_22_BOLD = QFont(FONT_STYLE, 22, QFont.Bold)

    FONT_24 = QFont(FONT_STYLE, 24)
    FONT_24_BOLD = QFont(FONT_STYLE, 24, QFont.Bold)

    FONT_26 = QFont(FONT_STYLE, 26)
    FONT_26_BOLD = QFont(FONT_STYLE, 26, QFont.Bold)

    FONT_28 = QFont(FONT_STYLE, 28)
    FONT_28_BOLD = QFont(FONT_STYLE, 28, QFont.Bold)

    FONT_32 = QFont(FONT_STYLE, 32)
    FONT_32_BOLD = QFont(FONT_STYLE, 32, QFont.Bold)

    FONT_36 = QFont(FONT_STYLE, 36)
    FONT_36_BOLD = QFont(FONT_STYLE, 36, QFont.Bold)

    FONT_40 = QFont(FONT_STYLE, 40)
    FONT_40_BOLD = QFont(FONT_STYLE, 40, QFont.Bold)

    FONT_45 = QFont(FONT_STYLE, 45)
    FONT_45_BOLD = QFont(FONT_STYLE, 45, QFont.Bold)

    @staticmethod
    def get_font(tp, size, is_bold=False):
        assert isinstance(tp, str)
        assert isinstance(size, int)
        if is_bold:
            ft = QFont(tp, size, QFont.Bold)
        else:
            ft = QFont(tp, size)
        return ft


class Color(object):
    white = "color: rgb(255,255,255);"
    red = "color: rgb(220, 20, 30);"
    green = "color: rgb(0, 220, 127);"
    blue = "color: rgb(70, 70, 255);"
    black = "color: rgb(0, 0, 0);"
    grey = "color: rgb(90, 90, 90);"
    yellow = "color: rgb(255, 200, 0);"
    c_window = "color: rgb(236, 236, 236);"
    purple = "color: rgb(255, 0, 255);"

    bg_white = "background-color: rgb(255, 255, 255);"
    bg_red = "background-color: rgb(220, 20, 30);"
    bg_grey = "background-color: rgb(150, 150, 150);"
    bg_litegrey = "background-color: rgb(240, 240, 240);"
    bg_green = "background-color: rgb(0, 220, 127);"
    bg_blue = "background-color: rgb(70, 70, 255);"
    bg_orange = "background-color: rgb(253, 200, 8);"
    bg_deep_orange = "background-color: rgb(227, 120, 46);"
    # bg_grey = "background-color: rgb(0, 0, 0);"
    bg_yellow = "background-color: rgb(255, 255, 0);"
    bg_window = "background-color: rgb(236, 236, 236);"
    bg_purple = "background-color: rgb(255, 0, 255);"

    state_running = "background-color: rgb(255, 255, 0);color: rgb(0, 0, 0);"
    state_fail = "background-color: rgb(220, 20, 30);color: rgb(255, 255, 255);"
    state_pass = "background-color: rgb(0, 220, 127);color: rgb(255, 255, 255);"
    state_disable = "background-color: rgb(150, 150, 150);color: rgb(255, 255, 255);"
    state_idle = "background-color: rgb(250, 250, 250);color: rgb(0, 0, 0);"

    leave_running = "background-color: rgb(255, 255, 100);color: rgb(0, 0, 0);"
    leave_fail = "background-color: rgb(250, 20, 30);color: rgb(255, 255, 255);"
    leave_pass = "background-color: rgb(0, 220, 154);color: rgb(255, 255, 255);"
    leave_disable = "background-color: rgb(160, 160, 160);color: rgb(255, 255, 255);"
    leave_idle = "background-color: rgb(255, 255, 255);color: rgb(0, 0, 0);"

    STATE_COLOR = {
        "RUNNING": "background-color: rgb(255, 255, 0);color: rgb(0, 0, 0);",
        "FAIL": "background-color: rgb(220, 20, 30);color: rgb(255, 255, 255);",
        "PASS": "background-color: rgb(0, 220, 127);color: rgb(255, 255, 255);",
        "DISABLE": "background-color: rgb(150, 150, 150);color: rgb(255, 255, 255);",
        "IDLE": "background-color: rgb(250, 250, 250);color: rgb(0, 0, 0);"
    }

    LEFT_COLOR = {
        "RUNNING": "background-color: rgb(255, 255, 100);color: rgb(0, 0, 0);",
        "FAIL": "background-color: rgb(250, 20, 30);color: rgb(255, 255, 255);",
        "PASS": "background-color: rgb(0, 220, 154);color: rgb(255, 255, 255);",
        "DISABLE": "background-color: rgb(160, 160, 160);color: rgb(255, 255, 255);",
        "IDLE": "background-color: rgb(255, 255, 255);color: rgb(0, 0, 0);"
    }

    @classmethod
    def get_color(cls, r, g, b):
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            return "color: rgb({},{},{});".format(r, g, b)

    @classmethod
    def get_background_color(cls, r, g, b):
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            return "background-color: rgb({},{},{});".format(r, g, b)


class QssStyle(object):
    TAB_WIDGET_STYLE = '''
QTabBar::tab {
        font-family:Arial;
        font-size:12px;
        spacing: 5px;
        border: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        color: black;
        background: rgb(200, 200, 200);
        height: 25px;
        min-width: 120px;
        margin-right: 2px;
        padding-left: 5px;
        padding-right: 5px;
}
QTabBar::tab:selected {
        color: white;
        background: rgb(0, 100, 255);
}
'''

    TAB_VIEW_STYLE = '''
QTableView {
   show-decoration-selected: 1;
    font: "Timers" ;
    font-size:  12px;
}

QTableView::item {
    border: 1px solid #d9d9d9;
    border-top-color: transparent;
    border-bottom-color: transparent;
}

QTableView::item:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
    border: 1px solid #bfcde4;
}

QTableView::item:selected {
    border: 1px solid #567dbc;
}

QTableView::item:selected:active{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);
}

QTableView::item:selected:!active {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);
}


QHeaderView{
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
    stop:0 rgba(230, 230, 230, 255),
    stop:1 rgba(250, 250, 250, 255));
    border: 1px solid #E6E6E6;
    min-height: 22px;
    font-size:  12px;
    font: bold large "Arial" ;
}
'''

