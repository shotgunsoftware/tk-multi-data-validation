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
from sgtk.platform.qt import QtGui, QtCore

from .api import ValidationManager
from .widgets import ValidationWidget

settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


class AppDialog(QtGui.QWidget):
    """
    The main Scene Data Validation App dialog.
    """

    #
    # Settings keys to save/restore
    #
    SETTINGS_WIDGET_GEOMETRY = "app_dialog_geometry"

    def __init__(self, parent=None):
        """
        Initialize the App dialog.

        :param parent: The parent QWidget for this dialog.
        :type parent: QtGui.QWidget
        """

        QtGui.QWidget.__init__(self, parent)

        self._bundle = sgtk.platform.current_bundle()

        # -----------------------------------------------------
        # Create validation manager

        self._manager = ValidationManager()

        # -----------------------------------------------------
        # Set up settings

        self._settings_manager = settings.UserSettings(self._bundle)

        # Define another QSettings object to store raw values. This is a work around for storing QByteArray objects in Python 3,
        # since the settings manager converts QByteArray objects to str, which causes an error when retrieving it and trying
        # to set the splitter state with a str instead of QByteArray object.
        self._raw_values_settings = QtCore.QSettings(
            "ShotGrid Software", "{app}_raw_values".format(app=self._bundle.name)
        )

        # -----------------------------------------------------
        # Set up UI

        # Requires the validation manager to alrady be creatd.
        self.setup_ui()

        # -----------------------------------------------------
        # Restore settings

        widget_geometry = self._raw_values_settings.value(
            self.SETTINGS_WIDGET_GEOMETRY, None
        )
        if widget_geometry:
            self.restoreGeometry(widget_geometry)

        self._validation_widget.restore_state(
            self._settings_manager, self._raw_values_settings
        )

        # -----------------------------------------------------
        # Log metric for app usage

        self._bundle._log_metric_viewed_app()

    def setup_ui(self):
        """
        Set up the UI manually (without a .ui file). This should only be called once.
        """

        # -----------------------------------------------------
        # Create the main validation widget

        self._validation_widget = ValidationWidget(self)

        # Connect signals between manager and widget
        self._manager.notifier.validate_rule_begin.connect(
            self._validation_widget.validate_rule_begin
        )
        self._manager.notifier.validate_rule_finished.connect(
            self._validation_widget.validate_rule_finished
        )
        self._manager.notifier.validate_all_finished.connect(
            self._validation_widget.validate_rule_finished
        )
        self._manager.notifier.resolve_rule_begin.connect(
            self._validation_widget.fix_rule_begin
        )
        self._manager.notifier.resolve_rule_finished.connect(
            self._validation_widget.fix_rule_finished
        )

        # NOTE hide the left-hand filter widget for now for simplicity
        self._validation_widget.turn_on_rule_type_filter(False)

        # TODO implement the functionality for validation -> publish and then this button can be shown
        self._validation_widget.publish_button.hide()

        # Override the default fix all method
        self._validation_widget.validate_callback = self._manager.validate_rules
        self._validation_widget.fix_callback = self._manager.resolve_rules

        self._validation_widget.set_validation_rules(
            self._manager.rules, self._manager.rule_types
        )

        # -----------------------------------------------------
        # Add the validation widget to this dialog's layout

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self._validation_widget)
        self.setLayout(main_layout)

    ######################################################################################################
    # Override Qt methods

    def closeEvent(self, event):
        """
        Overriden method triggered when the widget is closed.  Cleans up as much as possible
        to help the GC.

        :param event: Close event
        """

        # Save settings
        self._raw_values_settings.setValue(
            self.SETTINGS_WIDGET_GEOMETRY, self.saveGeometry()
        )
        self._validation_widget.save_state(
            self._settings_manager, self._raw_values_settings
        )

        return QtGui.QWidget.closeEvent(self, event)
