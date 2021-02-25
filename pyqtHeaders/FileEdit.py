# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Sourced from: https://www.reddit.com/r/learnpython/comments/97z5dq/pyqt5_drag_and_drop_file_option/

from PyQt5.QtWidgets import QMessageBox, QLineEdit
from PyQt5.QtGui import QIcon

import sys
import os


class FileEdit(QLineEdit):
    acceptedFiles = [".mp4",".webm",".mkv"]
    def __init__(self, parent):
        super(FileEdit, self).__init__(parent)

        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            filepath = str(urls[0].path())[1:]
            # any file type here

            self.setText(filepath)