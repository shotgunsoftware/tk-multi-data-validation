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

from ..utils.framework_qtwidgets import (
    SGQWidget,
    SGQLabel,
    SGQFrame,
    ShotgunSpinningWidget,
)


class ShotGridOverlayWidget(SGQWidget):
    """
    A flexible overlay widget that can display any combination of an image, title message and details text.

    TODO: migrate this to tk-framework-qtwidgets and potentially replace the existing ShotgunOverlayWidget
    with this one.
    """

    def __init__(self, parent=None):
        """
        Initialize the ShotGridOverlayWidget.
        """

        super(ShotGridOverlayWidget, self).__init__(
            parent, layout_direction=QtGui.QBoxLayout.TopToBottom
        )

        # Set the default image size to None - no scaling will be applied.
        self._image_size = None
        self._title_alignment = None
        self._title_word_wrap = True
        self._title_max_width = None

        # Set up the layout and widgets
        self._setup_ui()

        # Hook up a listener to the parent window so this widget follows along when the parent
        # window changes size
        filter = ResizeEventFilter(parent)
        filter.resized.connect(self._on_parent_resized)
        parent.installEventFilter(filter)

        # Initialize the overlay to be hidden
        self.hide()

    def _setup_ui(self):
        """
        Set up the layout and widgets in the overlay.
        """

        # The main frame for the overlay - used to set the background color
        frame = SGQFrame(self)
        frame.setAutoFillBackground(False)
        frame.setFrameShape(QtGui.QFrame.StyledPanel)
        frame.setFrameShadow(QtGui.QFrame.Raised)

        # The spinner widget displayed in a QLabel
        self._spinner_label = SGQLabel(frame)
        self._spinner = ShotgunSpinningWidget(self)

        # The image displayed in a QLabel
        self._image_label = SGQLabel(frame)
        self._image_label.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        )
        self._image_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        # The title text
        self._title_label = SGQLabel(frame)
        self._title_label.setTextFormat(QtCore.Qt.RichText)
        self._title_label.setOpenExternalLinks(True)
        self._title_label.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        )

        # The details text
        self._details_label = SGQLabel(frame)
        self._details_label.setTextFormat(QtCore.Qt.RichText)
        self._details_label.setWordWrap(True)
        self._details_label.setOpenExternalLinks(True)
        self._details_label.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.TextWordWrap
        )
        self._details_label.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        )

        # Add the image and title to a horizontal layout to control alignment relative to other content
        title_layout = QtGui.QHBoxLayout()
        title_layout.addWidget(self._image_label)
        title_layout.addWidget(self._title_label)
        title_layout.addWidget(self._spinner_label)

        # Add the details to a horizontal layout control alignment relative to other content
        details_layout = QtGui.QHBoxLayout()
        details_layout.setContentsMargins(0, 20, 0, 0)
        details_layout.addStretch()
        details_layout.addWidget(self._details_label)
        details_layout.addStretch()
        details_layout.setStretch(0, 1)
        details_layout.setStretch(1, 10)
        details_layout.setStretch(2, 1)

        # Add the title and details layout to a single layout
        content_layout = QtGui.QVBoxLayout()
        content_layout.addStretch()
        content_layout.addLayout(title_layout)
        content_layout.addLayout(details_layout)
        content_layout.addStretch()

        # Add grid layout to frame in order to add content widgets to the frame
        grid_layout = QtGui.QGridLayout(frame)
        grid_layout.addLayout(content_layout, 1, 1, 1, 1)

        # Add the frame to the overlay widget
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.add_widgets([frame])

    ##########################################################################################################
    # Properties

    @property
    def title_label(self):
        """
        Get the title QLabel that display the title message text.

        This object can be modified to customize the title label appearance.
        """
        return self._title_label

    @property
    def details_label(self):
        """
        Get the details QLabel that display the details info text.

        This object can be modified to customize the details label appearance.
        """
        return self._details_label

    @property
    def image_label(self):
        """
        Get the image QLabel that display the overlay image.

        This object can be modified to customize the image label appearance.
        """
        return self._image_label

    @property
    def image_size(self):
        """Get or set the image size."""
        return self._image_size

    @image_size.setter
    def image_size(self, size):
        self._image_size = size

    @property
    def title_alignment(self):
        """Get or set the title text alignment."""
        return self._title_alignment

    @title_alignment.setter
    def title_alignment(self, alignment):
        self._title_alignment = alignment

    @property
    def title_word_wrap(self):
        """Get or set the title text word wrap."""
        return self._title_word_wrap

    @title_word_wrap.setter
    def title_word_wrap(self, wrap):
        self._title_word_wrap = wrap

    @property
    def title_max_width(self):
        """Get or set the title text maximum width."""
        return self._title_max_width

    @title_max_width.setter
    def title_max_width(self, width):
        self._title_max_width = width

    ##########################################################################################################
    # Qt overridden methods

    def show(self):
        """
        Subclass the base method to show the overlay widget.
        """

        super(ShotGridOverlayWidget, self).show()

        # Ensure to resize the overlay according to its parent widget size.
        self._on_parent_resized()

    ##########################################################################################################
    # Public methods

    def show_message(self, title=None, image=None, details=None):
        """
        Show the overlay message with the given data.

        If certain data is not provided, the corresponding widgets will be hidden.

        NOTE: the same method name is used from the ShotgunOverlay widget to ease switching to use this new
        more generic and customizable overlay.
        """

        # Ensure the spinner is hdiden
        self.stop_spin()

        self._set_data(title=title, image=image, details=details)

        if title is None:
            self.title_label.hide()
        else:
            self.title_label.show()

        if image is None:
            self.image_label.hide()
        else:
            self.image_label.show()

        if details is None:
            self.details_label.hide()
        else:
            self.details_label.show()

        self.show()

    def show_error_message(self, title=None, image=None, details=None):
        """
        A convenience method to display the overlay message as an error.

        This is to help ease the transition to switching from the ShotgunOverlayWidget to this class.

        To customize the error message, call `show_message` with the title and/or details text
        already formatted using rich text. Use this method as an example to get you started.
        """

        if title:
            title = "<font style='color: #C8534A;'>{text}</font>".format(text=title)

        if details:
            details = "<font style='color: #C8534A;'>{text}</font>".format(text=details)

        self.show_message(title, image, details)

    def start_spin(self):
        """
        Show the SG spinner widget.
        """

        # Hide the other widgets
        self.image_label.hide()
        self.title_label.hide()
        self.details_label.hide()

        # Start the spinner and show the overlay
        self._spinner.start_spin()
        self.show()

    def stop_spin(self):
        """
        Stop the SG spinner widget.

        This method just hides the widget. To update the overlay widget, show_message must be
        called again with the data to show.
        """

        self._spinner_label.hide()
        self._spinner.hide()

    ##########################################################################################################
    # Protected methods

    def _set_data(self, image=None, title=None, details=None):
        """
        Set the overlay image, title and details data.

        The show method must be called to display the widget.

        :param image: The iamge to dispaly in the overlay.
        :type image: QIcon | QPixmap
        :param title: The title message text to display. This can be rich text to format and style the text.
        :type title: str
        :param details: The details info text to dispaly. This can be rich text to format and style the text.
        :type details: str
        """

        if isinstance(image, QtGui.QIcon):
            if self.image_size:
                pixmap = image.pixmap(self.image_size)
            else:
                size = image.availableSizes()[-1]
                pixmap = image.pixmap(size)
        elif isinstance(image, QtGui.QPixmap):
            pixmap = image
        else:
            pixmap = None

        if pixmap and self.image_size:
            pixmap = pixmap.scaled(self.image_size, QtCore.Qt.KeepAspectRatio)

        if title:
            if pixmap:
                if self._title_alignment is None:
                    self._title_label.setAlignment(
                        QtCore.Qt.AlignLeading
                        | QtCore.Qt.AlignLeft
                        | QtCore.Qt.AlignVCenter
                        | QtCore.Qt.TextWordWrap
                    )
                title_max_width = self.title_max_width or 250
            else:
                self._title_label.setAlignment(
                    QtCore.Qt.AlignCenter
                    | QtCore.Qt.AlignVCenter
                    | QtCore.Qt.TextWordWrap
                )
                title_max_width = self.title_max_width or 16777215

            self._title_label.setMaximumWidth(title_max_width)
            self._title_label.setWordWrap(self.title_word_wrap or False)

        self._image_label.setPixmap(pixmap)
        self._title_label.setText(title)
        self._details_label.setText(details)

    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.

        When associated widget is resized this slot is being called.
        """

        self.resize(self.parentWidget().size())

        self._spinner.resize(self.parentWidget().size())


class ResizeEventFilter(QtCore.QObject):
    """
    Utility and helper.

    Event filter which emits a resized signal whenever
    the monitored widget resizes.

    You use it like this:

    # create the filter object. Typically, it's
    # it's easiest to parent it to the object that is
    # being monitored (in this case self.ui.thumbnail)
    filter = ResizeEventFilter(self.ui.thumbnail)

    # now set up a signal/slot connection so that the
    # __on_thumb_resized slot gets called every time
    # the widget is resized
    filter.resized.connect(self.__on_thumb_resized)

    # finally, install the event filter into the QT
    # event system
    self.ui.thumbnail.installEventFilter(filter)
    """

    resized = QtCore.Signal()

    def eventFilter(self, obj, event):
        """
        Event filter implementation.
        For information, see the QT docs:
        http://doc.qt.io/qt-4.8/qobject.html#eventFilter

        This will emit the resized signal (in this class)
        whenever the linked up object is being resized.

        :param obj: The object that is being watched for events
        :param event: Event object that the object has emitted
        :returns: Always returns False to indicate that no events
                  should ever be discarded by the filter.
        """
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False
