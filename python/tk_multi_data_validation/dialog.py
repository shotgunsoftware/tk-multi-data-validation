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
from sgtk.platform.qt import QtGui

from .api import ValidationManager
from .widgets import ValidationWidget
from .utils.validation_notifier import ValidationNotifier

settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


class AppDialog(QtGui.QWidget):
    """
    The main Data Validation App dialog.
    """

    #
    # Settings keys to save/restore
    #
    SETTINGS_WIDGET_GEOMETRY = "app_dialog_geometry"

    # Notifier IDS for show/hide busy popup
    VALIDATE_ID = "validate"
    RESOLVE_ID = "resolve"

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

        self._manager = ValidationManager(notifier=ValidationNotifier(), has_ui=True)
        self._manager.accept_rule_fn = lambda rule: not rule.optional or rule.checked

        # -----------------------------------------------------
        # Set up settings

        self._settings_manager = settings.UserSettings(self._bundle)

        # -----------------------------------------------------
        # Set up UI

        # Requires the validation manager to alrady be creatd.
        self._setup_ui()
        self._connect_signals()

        # -----------------------------------------------------
        # Restore settings

        widget_geometry = self._settings_manager.retrieve(
            self.SETTINGS_WIDGET_GEOMETRY, None
        )
        if widget_geometry:
            self.restoreGeometry(widget_geometry)

        self._validation_widget.restore_state(self._settings_manager)

        # -----------------------------------------------------
        # Initialize app

        self._validation_widget.set_validation_rules(
            self._manager.rules, self._manager.rule_types
        )
        self._validation_widget.listen_for_events(True)

        # -----------------------------------------------------
        # Log metric for app usage

        self._bundle._log_metric_viewed_app()

    def _setup_ui(self):
        """
        Set up the UI manually (without a .ui file). This should only be called once.
        """

        # -----------------------------------------------------
        # Create the main validation widget

        self._validation_widget = ValidationWidget(self, group_rules_by="data_type")

        # NOTE hide the left-hand filter widget for now for simplicity
        self._validation_widget.turn_on_rule_type_filter(False)

        # TODO implement the functionality for validation -> publish and then this button can be shown
        self._validation_widget.publish_button.hide()

        # Set custom callbacks for validating/fix all and validating/fix individual rules
        self._validation_widget.validate_rules_callback = self._manager.validate_rules
        self._validation_widget.validate_all_callback = (
            lambda rules: self._manager.validate()
        )
        self._validation_widget.fix_rules_callback = (
            lambda rules: self._bundle.execute_hook_method(
                "hook_data_validation",
                "resolve_rules",
                manager=self._manager,
                rules=rules,
            )
        )
        self._validation_widget.fix_all_callback = (
            lambda rules: self._bundle.execute_hook_method(
                "hook_data_validation",
                "resolve_all_rules",
                manager=self._manager,
                rules=rules,
            )
        )

        # -----------------------------------------------------
        # Add the validation widget to this dialog's layout

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._validation_widget)
        self.setLayout(main_layout)

    def _connect_signals(self):
        """
        Set up Qt signals and slot connections.
        """

        # ------------------------------------------------------------
        # ValidationManager signals connected to the ValidationWidget

        # Connect signals from manager and widget
        self._manager.notifier.validate_rule_begin.connect(
            self._validation_widget.validate_rule_begin
        )
        self._manager.notifier.validate_rule_finished.connect(
            self._validation_widget.validate_rule_finished
        )
        self._manager.notifier.validate_all_begin.connect(
            self._validation_widget.validate_all_begin
        )
        self._manager.notifier.validate_all_finished.connect(
            self._validation_widget.validate_all_finished
        )
        self._manager.notifier.resolve_all_begin.connect(
            self._validation_widget.fix_all_begin
        )
        self._manager.notifier.resolve_all_finished.connect(
            self._validation_widget.fix_all_finished
        )
        self._manager.notifier.resolve_rule_begin.connect(
            self._validation_widget.fix_rule_begin
        )
        self._manager.notifier.resolve_rule_finished.connect(
            self._validation_widget.fix_rule_finished
        )

    ######################################################################################################
    # Override Qt methods

    def closeEvent(self, event):
        """
        Overriden method triggered when the widget is closed.  Cleans up as much as possible
        to help the GC.

        :param event: Close event
        """

        # Save settings
        self._settings_manager.store(
            self.SETTINGS_WIDGET_GEOMETRY, self.saveGeometry(), pickle_setting=False
        )
        self._validation_widget.save_state(self._settings_manager)

        return QtGui.QWidget.closeEvent(self, event)
