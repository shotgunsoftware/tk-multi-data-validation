# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.


import sgtk
from sgtk.platform.qt import QtCore, QtGui

from ..utils.framework_qtwidgets import SGQListView


class ListViewAutoHeight(SGQListView):
    """A QListView subclass to create a view whose height auto adjusts to the view contents."""

    def __init__(self, parent=None, height_padding=0):
        """
        Create the ListViewAutoHeight widget.

        :param parent: The parent widget
        :type parent: QtGui.QWidget
        :param height_padding: The padding to add to the size hint height.
        :type height_padding: int
        """

        super(ListViewAutoHeight, self).__init__(parent)

        self._height_padding = height_padding

    @property
    def height_padding(self):
        """Get or set the vertical padding to add to the height returned by the size hint method."""
        return self._height_padding

    @height_padding.setter
    def height_padding(self, padding):
        self._height_padding = padding

    def sizeHint(self):
        """
        Override the QListView method.

        Calculate the height of the view contents and return this value as the height size hint. This assumes
        that the rows of the view are uniform.

        :return: The size hint for the view.
        :rtype: QtCore.QSize
        """

        model = self.model()
        if not model:
            return QtCore.QSize(self.width(), self.height())

        rows = self.model().rowCount()
        if rows <= 0:
            return QtCore.QSize(self.width(), self.height())

        # This assumes all row heights are uniform. To support non-uniform row heights, every row in the view
        # needs to be checked, which could hurt the view's performance.
        height = rows * self.sizeHintForRow(0)
        height += self._height_padding

        return QtCore.QSize(self.width(), height)
